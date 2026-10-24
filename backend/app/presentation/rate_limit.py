"""
Sliding-window per-IP rate limiting for FastAPI presentation routes.
"""

from collections import defaultdict, deque
import math
import threading
import time
from fastapi import HTTPException, Request, status


def extract_client_ip(request: Request) -> str:
    """
    Resolve the originating client IP address from X-Forwarded-For or the socket peer.
    """
    forwarded_for = request.headers.get("X-Forwarded-For", "").strip()
    if forwarded_for:
        first_hop = forwarded_for.split(",")[0].strip()
        if first_hop:
            return first_hop
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


class SlidingWindowRateLimiter:
    """
    Thread-safe in-memory sliding-window rate limiter keyed by client IP address.
    """

    def __init__(self, max_requests: int, window_seconds: int = 60) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._buckets: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, client_ip: str) -> None:
        """
        Record a request for client_ip or raise HTTP 429 if the window quota is exhausted.
        """
        now = time.monotonic()
        cutoff = now - self._window_seconds

        with self._lock:
            bucket = self._buckets[client_ip]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= self._max_requests:
                oldest = bucket[0]
                retry_after = max(
                    1, math.ceil(self._window_seconds - (now - oldest))
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please wait before trying again.",
                    headers={"Retry-After": str(retry_after)},
                )

            bucket.append(now)

    def reset(self) -> None:
        """Clear all tracked request timestamps."""
        with self._lock:
            self._buckets.clear()

    def __call__(self, request: Request) -> None:
        """FastAPI dependency entrypoint."""
        client_ip = extract_client_ip(request)
        self.check(client_ip)
