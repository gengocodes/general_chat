export interface StructuredErrorDetail {
  code?: string;
  message?: string;
}

export interface FastApiErrorPayload {
  detail?: string | StructuredErrorDetail;
}
