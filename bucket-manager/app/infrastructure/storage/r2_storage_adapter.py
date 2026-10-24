"""Cloudflare R2 S3-compatible storage adapter implementing ObjectStoragePort."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import logging
import urllib.parse
import httpx

from app.domain.entities.object_item import PresignedDownload, StoredObject
from app.domain.errors import ObjectNotFoundError, StorageProviderError
from app.application.ports.object_storage_port import ObjectStoragePort

logger = logging.getLogger(__name__)

EMPTY_PAYLOAD_SHA256 = hashlib.sha256(b"").hexdigest()


def _hmac_sha256(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _derive_signing_key(secret_key: str, date_stamp: str) -> bytes:
    k_date = _hmac_sha256(("AWS4" + secret_key).encode("utf-8"), date_stamp)
    k_region = _hmac_sha256(k_date, "auto")
    k_service = _hmac_sha256(k_region, "s3")
    return _hmac_sha256(k_service, "aws4_request")


def _sign_canonical_request(
    secret_key: str,
    date_stamp: str,
    amz_date: str,
    credential_scope: str,
    canonical_request: str,
) -> str:
    """Compute the AWS4-HMAC-SHA256 hex signature for a canonical S3 request."""
    string_to_sign = "\n".join(
        [
            "AWS4-HMAC-SHA256",
            amz_date,
            credential_scope,
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
        ]
    )
    signing_key = _derive_signing_key(secret_key, date_stamp)
    return hmac.new(
        signing_key, string_to_sign.encode("utf-8"), hashlib.sha256
    ).hexdigest()


@dataclass(frozen=True)
class _R2Credentials:
    """Internal value object grouping Cloudflare R2 connection credentials."""

    endpoint_url: str
    host: str
    access_key: str
    secret_key: str
    bucket: str


class R2StorageAdapter(ObjectStoragePort):
    """ObjectStoragePort implementation backed by Cloudflare R2 (S3 SigV4 REST API)."""

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        endpoint_url: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
        presigned_expiry_seconds: int = 900,
        retention_hours: int = 24,
        http_client: httpx.Client | None = None,
    ):
        clean_endpoint = endpoint_url.rstrip("/")
        self._creds = _R2Credentials(
            endpoint_url=clean_endpoint,
            host=urllib.parse.urlparse(clean_endpoint).netloc,
            access_key=access_key_id,
            secret_key=secret_access_key,
            bucket=bucket_name,
        )
        self._presigned_expiry = presigned_expiry_seconds
        self._retention_hours = retention_hours
        self._client = http_client or httpx.Client(timeout=30.0)

    def _canonical_uri(self, object_key: str) -> str:
        encoded_key = urllib.parse.quote(object_key, safe="-_.~")
        return f"/{self._creds.bucket}/{encoded_key}"

    def _object_url(self, object_key: str) -> str:
        return f"{self._creds.endpoint_url}{self._canonical_uri(object_key)}"

    def _build_signed_headers(
        self,
        method: str,
        object_key: str,
        payload_hash: str,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, str]:
        """Compute AWS Signature Version 4 headers for a direct R2 HTTP request."""
        now = datetime.now(timezone.utc)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")
        credential_scope = f"{date_stamp}/auto/s3/aws4_request"

        headers: dict[str, str] = {
            "host": self._creds.host,
            "x-amz-content-sha256": payload_hash,
            "x-amz-date": amz_date,
        }
        if extra_headers:
            headers.update({k.lower(): v.strip() for k, v in extra_headers.items()})

        sorted_keys = sorted(headers.keys())
        signed_headers = ";".join(sorted_keys)
        canonical_request = "\n".join(
            [
                method,
                self._canonical_uri(object_key),
                "",
                "".join(f"{k}:{headers[k]}\n" for k in sorted_keys),
                signed_headers,
                payload_hash,
            ]
        )
        signature = _sign_canonical_request(
            self._creds.secret_key,
            date_stamp,
            amz_date,
            credential_scope,
            canonical_request,
        )
        headers["Authorization"] = (
            f"AWS4-HMAC-SHA256 Credential={self._creds.access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )
        return headers

    def _generate_presigned_get_url(self, object_key: str) -> str:
        """Generate an S3 SigV4 presigned GET URL for downloading object_key from R2."""
        now = datetime.now(timezone.utc)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")
        credential_scope = f"{date_stamp}/auto/s3/aws4_request"

        query_params = {
            "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
            "X-Amz-Credential": f"{self._creds.access_key}/{credential_scope}",
            "X-Amz-Date": amz_date,
            "X-Amz-Expires": str(self._presigned_expiry),
            "X-Amz-SignedHeaders": "host",
            "response-content-disposition": f'attachment; filename="{object_key}"',
        }
        canonical_querystring = urllib.parse.urlencode(
            sorted(query_params.items()), quote_via=urllib.parse.quote
        )
        canonical_uri = self._canonical_uri(object_key)
        canonical_request = "\n".join(
            [
                "GET",
                canonical_uri,
                canonical_querystring,
                f"host:{self._creds.host}\n",
                "host",
                "UNSIGNED-PAYLOAD",
            ]
        )
        signature = _sign_canonical_request(
            self._creds.secret_key,
            date_stamp,
            amz_date,
            credential_scope,
            canonical_request,
        )
        return (
            f"{self._creds.endpoint_url}{canonical_uri}"
            f"?{canonical_querystring}&X-Amz-Signature={signature}"
        )

    def _object_exists(self, object_key: str) -> bool:
        """Check whether an object key exists in R2 via HTTP HEAD."""
        headers = self._build_signed_headers("HEAD", object_key, EMPTY_PAYLOAD_SHA256)
        try:
            res = self._client.head(self._object_url(object_key), headers=headers)
        except httpx.HTTPError as exc:
            logger.exception("R2 HEAD request failed for %s: %s", object_key, str(exc))
            raise StorageProviderError("Failed to verify object in storage.") from exc

        if res.status_code == 404:
            return False
        if not res.is_success:
            raise StorageProviderError("Failed to verify object in storage.")
        return True

    def put_object(
        self,
        object_key: str,
        original_name: str,
        content: bytes,
        content_type: str,
    ) -> StoredObject:
        # TODO: Remove 24-hour auto-expiration / R2 bucket lifecycle rule if permanent retention is needed. # pylint: disable=fixme,line-too-long
        expires_at = datetime.now(timezone.utc) + timedelta(hours=self._retention_hours)
        payload_hash = hashlib.sha256(content).hexdigest()
        extra_headers = {
            "content-type": content_type,
            "x-amz-meta-original-name": original_name,
            "x-amz-meta-expires-at": expires_at.isoformat(),
        }
        headers = self._build_signed_headers(
            "PUT", object_key, payload_hash, extra_headers
        )

        try:
            res = self._client.put(
                self._object_url(object_key), content=content, headers=headers
            )
        except httpx.HTTPError as exc:
            logger.exception("Failed to upload object %s to R2: %s", object_key, str(exc))
            raise StorageProviderError("Failed to store object in bucket.") from exc

        if not res.is_success:
            logger.error("R2 PUT returned %d: %s", res.status_code, res.text)
            raise StorageProviderError("Failed to store object in bucket.")

        download_url = self._generate_presigned_get_url(object_key)
        logger.info(
            "Stored object in R2: key=%s (%d bytes, expires=%s)",
            object_key,
            len(content),
            expires_at.isoformat(),
        )
        return StoredObject(
            object_key=object_key,
            original_name=original_name,
            size_bytes=len(content),
            download_url=download_url,
            expires_at=expires_at,
        )

    def create_presigned_download(self, object_key: str) -> PresignedDownload:
        if not self._object_exists(object_key):
            raise ObjectNotFoundError(f"Object '{object_key}' does not exist.")
        download_url = self._generate_presigned_get_url(object_key)
        return PresignedDownload(
            object_key=object_key,
            download_url=download_url,
            expires_in_seconds=self._presigned_expiry,
        )

    def get_object_bytes(self, object_key: str) -> bytes:
        headers = self._build_signed_headers("GET", object_key, EMPTY_PAYLOAD_SHA256)
        try:
            res = self._client.get(self._object_url(object_key), headers=headers)
        except httpx.HTTPError as exc:
            logger.exception("R2 GET failed for %s: %s", object_key, str(exc))
            raise StorageProviderError("Failed to retrieve object from bucket.") from exc

        if res.status_code == 404:
            raise ObjectNotFoundError(f"Object '{object_key}' does not exist.")
        if not res.is_success:
            raise StorageProviderError("Failed to retrieve object from bucket.")
        return res.content

    def delete_object(self, object_key: str) -> None:
        if not self._object_exists(object_key):
            raise ObjectNotFoundError(f"Object '{object_key}' does not exist.")
        headers = self._build_signed_headers("DELETE", object_key, EMPTY_PAYLOAD_SHA256)
        try:
            res = self._client.delete(self._object_url(object_key), headers=headers)
        except httpx.HTTPError as exc:
            logger.exception("Failed to delete object %s from R2: %s", object_key, str(exc))
            raise StorageProviderError("Failed to delete object from bucket.") from exc

        if not res.is_success:
            raise StorageProviderError("Failed to delete object from bucket.")
        logger.info("Deleted object from R2: key=%s", object_key)
