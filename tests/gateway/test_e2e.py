"""Tests for Steps 12.8-12.10 end-to-end communication and delivery."""

import unittest

from legacy_gateway.device import DeviceProfile, SimulatedDevice
from legacy_gateway.gateway import Gateway
from legacy_gateway.gateway.e2e import EndToEndHarness
from legacy_gateway.protocol.messages import RequestMessage, RequestStatus, ResponseMessage
from legacy_gateway.providers import MockMode, MockProvider


class LongResponseProvider:
    """Deterministic provider used only to exercise E2E chunk delivery."""

    def __init__(self, content: str) -> None:
        self.content = content
        self.execute_count = 0

    def execute(self, request: RequestMessage) -> ResponseMessage:
        self.execute_count += 1
        return ResponseMessage(
            request_id=request.request_id,
            status=RequestStatus.SUCCESS,
            content=self.content,
            provider="test-long-response",
            model=request.model,
            finish_reason="test_complete",
        )


class EndToEndTests(unittest.TestCase):
    def make_device(self) -> SimulatedDevice:
        return SimulatedDevice(DeviceProfile(device_id="SIM-E2E"))

    def test_successful_device_gateway_provider_device_path(self) -> None:
        provider = MockProvider()
        device = self.make_device()
        harness = EndToEndHarness.with_mock_provider(device, provider)

        response = harness.send_chat("hello gateway")

        self.assertEqual(response.status, RequestStatus.SUCCESS)
        self.assertEqual(response.request_id, "SIM-E2E-R-1")
        self.assertEqual(response.content, "MOCK_RESPONSE:chat")
        self.assertIs(device.last_response, response)
        self.assertEqual(provider.execute_count, 1)

    def test_second_request_gets_new_request_id(self) -> None:
        device = self.make_device()
        harness = EndToEndHarness.with_mock_provider(device)

        first = harness.send_chat("one")
        second = harness.send_chat("two")

        self.assertEqual(first.request_id, "SIM-E2E-R-1")
        self.assertEqual(second.request_id, "SIM-E2E-R-2")
        self.assertEqual(len(device.response_history), 2)

    def test_provider_failure_returns_to_device(self) -> None:
        device = self.make_device()
        provider = MockProvider(MockMode.FAILURE)
        harness = EndToEndHarness.with_mock_provider(device, provider)

        response = harness.send_chat("failure test")

        self.assertEqual(response.status, RequestStatus.FAILURE)
        self.assertEqual(response.error["code"], "PROVIDER_ERROR")
        self.assertIs(device.last_response, response)

    def test_unknown_provider_outcome_reaches_device_as_uncertain(self) -> None:
        device = self.make_device()
        provider = MockProvider(MockMode.UNKNOWN)
        harness = EndToEndHarness.with_mock_provider(device, provider)

        response = harness.send_chat("unknown test")

        self.assertEqual(response.status, RequestStatus.UNCERTAIN)
        self.assertEqual(response.error["code"], "UNKNOWN_OUTCOME")

    def test_response_limit_is_enforced_at_device_boundary(self) -> None:
        device = SimulatedDevice(
            DeviceProfile(device_id="SIM-E2E", max_response_chars=5)
        )
        harness = EndToEndHarness.with_mock_provider(device)

        with self.assertRaises(ValueError):
            harness.send_chat("hello")

    def test_large_success_response_is_chunked_and_reassembled_e2e(self) -> None:
        content = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        device = SimulatedDevice(
            DeviceProfile(
                device_id="SIM-E2E",
                max_response_chars=len(content),
                response_chunk_size=4,
            )
        )
        provider = LongResponseProvider(content)
        harness = EndToEndHarness(device=device, gateway=Gateway(provider))

        response = harness.send_chat("chunk me")

        self.assertEqual(response.content, content)
        self.assertIsNotNone(device.last_response)
        self.assertEqual(device.last_response.content, content)
        self.assertEqual(len(device.response_history), 1)
        self.assertEqual(provider.execute_count, 1)


if __name__ == "__main__":
    unittest.main()
