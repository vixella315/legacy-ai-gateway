"""Tests for Step 12.5 gateway core."""

import unittest

from legacy_gateway.gateway import Gateway
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


def make_request() -> RequestMessage:
    return RequestMessage(
        request_id="R-12-5",
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
        response = Gateway(provider).handle_request(make_request())
        self.assertEqual(response.status, RequestStatus.SUCCESS)
        self.assertEqual(response.request_id, "R-12-5")
        self.assertEqual(response.content, "MOCK_RESPONSE:chat")
        self.assertEqual(provider.execute_count, 1)

    def test_invalid_request_is_rejected_before_provider(self) -> None:
        provider = MockProvider()
        request = RequestMessage(
            request_id="",
            session_id="S-1",
            device_id="D-1",
            operation="chat",
        )
        with self.assertRaises(ValueError):
            Gateway(provider).handle_request(request)
        self.assertEqual(provider.execute_count, 0)

    def test_timeout_becomes_uncertain(self) -> None:
        response = Gateway(
            MappedErrorProvider(ProviderTimeout("timed out"))
        ).handle_request(make_request())
        self.assertEqual(response.status, RequestStatus.UNCERTAIN)
        self.assertEqual(response.error["code"], "TIMEOUT")

    def test_unknown_outcome_becomes_uncertain(self) -> None:
        response = Gateway(
            MappedErrorProvider(ProviderUnknownOutcome("unknown"))
        ).handle_request(make_request())
        self.assertEqual(response.status, RequestStatus.UNCERTAIN)
        self.assertEqual(response.error["code"], "UNKNOWN_OUTCOME")

    def test_rate_limit_becomes_failure(self) -> None:
        response = Gateway(
            MappedErrorProvider(ProviderRateLimited("limited"))
        ).handle_request(make_request())
        self.assertEqual(response.status, RequestStatus.FAILURE)
        self.assertEqual(response.error["code"], "RATE_LIMITED")

    def test_unavailable_becomes_failure(self) -> None:
        response = Gateway(
            MappedErrorProvider(ProviderUnavailable("offline"))
        ).handle_request(make_request())
        self.assertEqual(response.status, RequestStatus.FAILURE)
        self.assertEqual(response.error["code"], "PROVIDER_UNAVAILABLE")

    def test_generic_provider_error_becomes_failure(self) -> None:
        response = Gateway(
            MappedErrorProvider(ProviderError("provider failed"))
        ).handle_request(make_request())
        self.assertEqual(response.status, RequestStatus.FAILURE)
        self.assertEqual(response.error["code"], "PROVIDER_ERROR")

    def test_malformed_provider_response_is_rejected(self) -> None:
        response = Gateway(MockProvider(MockMode.MALFORMED)).handle_request(make_request())
        self.assertEqual(response.status, RequestStatus.FAILURE)
        self.assertEqual(response.error["code"], "PROVIDER_PROTOCOL_ERROR")

    def test_request_id_mismatch_is_rejected(self) -> None:
        response = Gateway(WrongRequestIdProvider()).handle_request(make_request())
        self.assertEqual(response.status, RequestStatus.FAILURE)
        self.assertEqual(response.error["code"], "REQUEST_ID_MISMATCH")

    def test_gateway_does_not_retry_provider_error(self) -> None:
        provider = MockProvider(MockMode.FAILURE)
        response = Gateway(provider).handle_request(make_request())
        self.assertEqual(response.status, RequestStatus.FAILURE)
        self.assertEqual(provider.execute_count, 1)


if __name__ == "__main__":
    unittest.main()
