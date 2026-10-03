"""Core provider-facing gateway logic for Prototype 1.

Step 12.5 stays in-process. Request lifecycle tracking is integrated here so
Step 12.6 is part of the actual execution path. Authentication, durable
storage, cost accounting, networking, and retry/recovery remain later stages.
"""

from __future__ import annotations

from legacy_gateway.gateway.requests import RequestLifecycle, RequestTracker
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

    def __init__(
        self,
        provider: ProviderAdapter,
        request_tracker: RequestTracker | None = None,
    ) -> None:
        self.provider = provider
        self.request_tracker = request_tracker or RequestTracker()

    def handle_request(self, request: RequestMessage) -> ResponseMessage:
        """Validate, track, execute, normalize, and validate one provider response."""
        validate_request(request)

        record = self.request_tracker.create(request)
        record.transition(RequestLifecycle.RECEIVED)

        # Prototype 1 has no authentication or cost-control implementation yet.
        # These lifecycle markers represent the approved state-machine gates;
        # they do not claim those future controls are already implemented.
        record.transition(RequestLifecycle.AUTHORIZED)
        record.transition(RequestLifecycle.COST_CHECKED)
        record.transition(RequestLifecycle.RUNNING)

        try:
            response = self.provider.execute(request)
        except ProviderTimeout as exc:
            response = self._error_response(
                request, RequestStatus.UNCERTAIN, "TIMEOUT", str(exc)
            )
        except ProviderUnknownOutcome as exc:
            response = self._error_response(
                request, RequestStatus.UNCERTAIN, "UNKNOWN_OUTCOME", str(exc)
            )
        except ProviderRateLimited as exc:
            response = self._error_response(
                request, RequestStatus.FAILURE, "RATE_LIMITED", str(exc)
            )
        except ProviderUnavailable as exc:
            response = self._error_response(
                request, RequestStatus.FAILURE, "PROVIDER_UNAVAILABLE", str(exc)
            )
        except ProviderError as exc:
            response = self._error_response(
                request, RequestStatus.FAILURE, "PROVIDER_ERROR", str(exc)
            )

        if not isinstance(response, ResponseMessage):
            response = self._error_response(
                request,
                RequestStatus.FAILURE,
                "PROVIDER_PROTOCOL_ERROR",
                "provider returned an unsupported response object",
            )
        else:
            try:
                validate_response(response)
            except ProtocolValidationError as exc:
                response = self._error_response(
                    request, RequestStatus.FAILURE, "PROVIDER_PROTOCOL_ERROR", str(exc)
                )
            else:
                if response.request_id != request.request_id:
                    response = self._error_response(
                        request,
                        RequestStatus.FAILURE,
                        "REQUEST_ID_MISMATCH",
                        "provider response request_id does not match request",
                    )

        self._record_terminal_state(request.request_id, response.status)
        return response

    def _record_terminal_state(
        self,
        request_id: str,
        status: RequestStatus,
    ) -> None:
        state_by_status = {
            RequestStatus.SUCCESS: RequestLifecycle.SUCCESS,
            RequestStatus.FAILURE: RequestLifecycle.FAILURE,
            RequestStatus.UNCERTAIN: RequestLifecycle.UNCERTAIN,
        }
        self.request_tracker.transition(request_id, state_by_status[status])

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
