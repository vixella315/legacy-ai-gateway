"""Tests for Step 12.5 gateway core and Step 12.13-QF-001 integration."""

import unittest

from legacy_gateway.gateway import Gateway, RequestLifecycle
from legacy_gateway.protocol.messages import RequestMessage, RequestStatus, ResponseMessage
from legacy_gateway.providers import (
    MockMode,
    MockProvider,
    ProviderError,
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnknownOutcome,
    ProviderUnavailable,
)


def make_request(request_id: str = "R-12-5") -> RequestMessage:
    return RequestMessage(
        request_id=request_id,
        session_id="S-1",
        device_id="D-1",
        operation="chat",
        model="mock-model",
    )


class MappedErrorProvider:
    def __init__(self, error: ProviderError) -> None:
        self.error = error

    def identity(self):
        return MockProvider().identity()

    def execute(self, request):
        raise self.error


class WrongRequestIdProvider:
    def identity(self):
        return MockProvider().identity()

    def execute(self, request):
        return ResponseMessage(
            request_id="WRONG-ID",
            status=RequestStatus.SUCCESS,
            content="bad response",
            provider="test",
        )


class GatewayCoreTests(unittest.TestCase):
    def test_success_reaches_provider_and_returns_response(self) -> None:
        provider = MockProvider()
        gateway = Gateway(provider)
        response = gateway.handle_request(make_request())
        self.assertEqual(response.status, RequestStatus.SUCCESS)
        self.assertEqual(response.request_id, "R-12-5")
        self.assertEqual(response.content, "MOCK_RESPONSE:chat")
        self.assertEqual(provider.execute_count, 1)

        record = gateway.request_tracker.require("R-12-5")
        self.assertEqual(
            record.history,
            [
                RequestLifecycle.NEW,
                RequestLifecycle.RECEIVED,
                RequestLifecycle.AUTHORIZED,
                RequestLifecycle.COST_CHECKED,
                RequestLifecycle.RUNNING,
                RequestLifecycle.SUCCESS,
            ],
        )

    def test_invalid_request_is_rejected_before_provider_or_tracking(self) -> None:
        provider = MockProvider()
        gateway = Gateway(provider)
        request = RequestMessage(
            request_id="",
            session_id="S-1",
            device_id="D-1",
            operation="chat",
        )
        with self.assertRaises(ValueError):
            gateway.handle_request(request)
        self.assertEqual(provider.execute_count, 0)
        self.assertEqual(len(gateway.request_tracker), 0)

    def test_duplicate_request_id_is_rejected_before_second_provider_execution(self) -> None:
        provider = MockProvider()
        gateway = Gateway(provider)
        request = make_request()

        first = gateway.handle_request(request)

        with self.assertRaises(ValueError):
            gateway.handle_request(request)

        self.assertEqual(first.status, RequestStatus.SUCCESS)
        self.assertEqual(provider.execute_count, 1)
        self.assertEqual(
            gateway.request_tracker.require(request.request_id).state,
            RequestLifecycle.SUCCESS,
        )

    def test_timeout_becomes_uncertain_and_tracks_terminal_state(self) -> None:
        gateway = Gateway(MappedErrorProvider(ProviderTimeout("timed out")))
        response = gateway.handle_request(make_request())
        self.assertEqual(response.status, RequestStatus.UNCERTAIN)
        self.assertEqual(response.error["code"], "TIMEOUT")
        self.assertEqual(
            gateway.request_tracker.require("R-12-5").state,
            RequestLifecycle.UNCERTAIN,
        )

    def test_unknown_outcome_becomes_uncertain(self) -> None:
        gateway = Gateway(MappedErrorProvider(ProviderUnknownOutcome("unknown")))
        response = gateway.handle_request(make_request())
        self.assertEqual(response.status, RequestStatus.UNCERTAIN)
        self.assertEqual(response.error["code"], "UNKNOWN_OUTCOME")
        self.assertEqual(
            gateway.request_tracker.require("R-12-5").state,
            RequestLifecycle.UNCERTAIN,
        )

    def test_rate_limit_becomes_failure(self) -> None:
        gateway = Gateway(MappedErrorProvider(ProviderRateLimited("limited")))
        response = gateway.handle_request(make_request())
        self.assertEqual(response.status, RequestStatus.FAILURE)
        self.assertEqual(response.error["code"], "RATE_LIMITED")
        self.assertEqual(
            gateway.request_tracker.require("R-12-5").state,
            RequestLifecycle.FAILURE,
        )

    def test_unavailable_becomes_failure(self) -> None:
        gateway = Gateway(MappedErrorProvider(ProviderUnavailable("offline")))
        response = gateway.handle_request(make_request())
        self.assertEqual(response.status, RequestStatus.FAILURE)
        self.assertEqual(response.error["code"], "PROVIDER_UNAVAILABLE")
        self.assertEqual(
            gateway.request_tracker.require("R-12-5").state,
            RequestLifecycle.FAILURE,
        )

    def test_generic_provider_error_becomes_failure(self) -> None:
        gateway = Gateway(MappedErrorProvider(ProviderError("provider failed")))
        response = gateway.handle_request(make_request())
        self.assertEqual(response.status, RequestStatus.FAILURE)
        self.assertEqual(response.error["code"], "PROVIDER_ERROR")
        self.assertEqual(
            gateway.request_tracker.require("R-12-5").state,
            RequestLifecycle.FAILURE,
        )

    def test_malformed_provider_response_is_rejected(self) -> None:
        gateway = Gateway(MockProvider(MockMode.MALFORMED))
        response = gateway.handle_request(make_request())
        self.assertEqual(response.status, RequestStatus.FAILURE)
        self.assertEqual(response.error["code"], "PROVIDER_PROTOCOL_ERROR")
        self.assertEqual(
            gateway.request_tracker.require("R-12-5").state,
            RequestLifecycle.FAILURE,
        )

    def test_request_id_mismatch_is_rejected(self) -> None:
        gateway = Gateway(WrongRequestIdProvider())
        response = gateway.handle_request(make_request())
        self.assertEqual(response.status, RequestStatus.FAILURE)
        self.assertEqual(response.error["code"], "REQUEST_ID_MISMATCH")
        self.assertEqual(
            gateway.request_tracker.require("R-12-5").state,
            RequestLifecycle.FAILURE,
        )

    def test_gateway_does_not_retry_provider_error(self) -> None:
        provider = MockProvider(MockMode.FAILURE)
        gateway = Gateway(provider)
        response = gateway.handle_request(make_request())
        self.assertEqual(response.status, RequestStatus.FAILURE)
        self.assertEqual(provider.execute_count, 1)
        self.assertEqual(
            gateway.request_tracker.require("R-12-5").state,
            RequestLifecycle.FAILURE,
        )


if __name__ == "__main__":
    unittest.main()
