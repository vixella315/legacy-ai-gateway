"""Core provider-facing gateway logic for Prototype 1.

Step 12.5 intentionally stays in-process. Networking, authentication,
durable request state, cost accounting, and retry/recovery belong to later
milestones.
"""

from __future__ import annotations

from legacy_gateway.protocol.messages import RequestMessage, RequestStatus, ResponseMessage
from legacy_gateway.protocol.validation import ProtocolValidationError, validate_request, validate_response
from legacy_gateway.providers.interface import (
    ProviderAdapter,
    ProviderError,
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnavailable,
    ProviderUnknownOutcome,
)


class Gateway:
    """Route one validated logical request to one configured provider."""

    def __init__(self, provider: ProviderAdapter) -> None:
        self.provider = provider

    def handle_request(self, request: RequestMessage) -> ResponseMessage:
        """Validate, execute, normalize, and validate one provider response."""
        validate_request(request)

        try:
            response = self.provider.execute(request)
        except ProviderTimeout as exc:
            return self._error_response(request, RequestStatus.UNCERTAIN, "TIMEOUT", str(exc))
        except ProviderUnknownOutcome as exc:
            return self._error_response(
                request, RequestStatus.UNCERTAIN, "UNKNOWN_OUTCOME", str(exc)
            )
        except ProviderRateLimited as exc:
            return self._error_response(
                request, RequestStatus.FAILURE, "RATE_LIMITED", str(exc)
            )
        except ProviderUnavailable as exc:
            return self._error_response(
                request, RequestStatus.FAILURE, "PROVIDER_UNAVAILABLE", str(exc)
            )
        except ProviderError as exc:
            return self._error_response(
                request, RequestStatus.FAILURE, "PROVIDER_ERROR", str(exc)
            )

        if not isinstance(response, ResponseMessage):
            return self._error_response(
                request,
                RequestStatus.FAILURE,
                "PROVIDER_PROTOCOL_ERROR",
                "provider returned an unsupported response object",
            )

        try:
            validate_response(response)
        except ProtocolValidationError as exc:
            return self._error_response(
                request, RequestStatus.FAILURE, "PROVIDER_PROTOCOL_ERROR", str(exc)
            )

        if response.request_id != request.request_id:
            return self._error_response(
                request,
                RequestStatus.FAILURE,
                "REQUEST_ID_MISMATCH",
                "provider response request_id does not match request",
            )

        return response

    @staticmethod
    def _error_response(
        request: RequestMessage,
        status: RequestStatus,
        code: str,
        message: str,
    ) -> ResponseMessage:
        return ResponseMessage(
            request_id=request.request_id,
            status=status,
            error={"code": code, "message": message},
            provider="gateway",
            finish_reason="gateway_error",
        )
