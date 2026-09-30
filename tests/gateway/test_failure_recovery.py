"""Tests for Step 12.9 failure and recovery."""

import unittest

from legacy_gateway.device import DeviceProfile, SimulatedDevice
from legacy_gateway.gateway.e2e import EndToEndHarness
from legacy_gateway.protocol.messages import RequestStatus
from legacy_gateway.providers import MockMode, MockProvider


class FailureRecoveryTests(unittest.TestCase):
    def make_device(self) -> SimulatedDevice:
        return SimulatedDevice(DeviceProfile(device_id="SIM-RECOVERY"))

    def test_provider_failure_is_not_retried(self) -> None:
        provider = MockProvider(MockMode.FAILURE)
        harness = EndToEndHarness.with_mock_provider(self.make_device(), provider)
        request = harness.create_request("failure")
        response = harness.execute(request)
        self.assertEqual(response.status, RequestStatus.FAILURE)
        self.assertEqual(provider.execute_count, 1)

    def test_unknown_outcome_is_not_automatically_retried(self) -> None:
        provider = MockProvider(MockMode.UNKNOWN)
        harness = EndToEndHarness.with_mock_provider(self.make_device(), provider)
        request = harness.create_request("unknown")
        response = harness.execute(request)
        self.assertEqual(response.status, RequestStatus.UNCERTAIN)
        self.assertEqual(response.request_id, request.request_id)
        self.assertEqual(provider.execute_count, 1)

    def test_lost_delivery_can_be_recovered_without_provider_retry(self) -> None:
        provider = MockProvider()
        device = self.make_device()
        harness = EndToEndHarness.with_mock_provider(device, provider)
        request = harness.create_request("delivery")
        response = harness.execute(request)
        self.assertEqual(provider.execute_count, 1)
        self.assertEqual(device.response_history, [])
        harness.recover_delivery(response)
        self.assertEqual(provider.execute_count, 1)
        self.assertIs(device.last_response, response)
        self.assertEqual(device.response_history, [response])

    def test_recovery_preserves_request_identity(self) -> None:
        provider = MockProvider()
        device = self.make_device()
        harness = EndToEndHarness.with_mock_provider(device, provider)
        request = harness.create_request("identity")
        response = harness.execute(request)
        harness.recover_delivery(response)
        self.assertEqual(response.request_id, request.request_id)
        self.assertEqual(provider.execute_count, 1)

    def test_recovery_does_not_create_second_ai_result(self) -> None:
        provider = MockProvider()
        device = self.make_device()
        harness = EndToEndHarness.with_mock_provider(device, provider)
        request = harness.create_request("same-operation")
        response = harness.execute(request)
        harness.recover_delivery(response)
        self.assertEqual(len(device.response_history), 1)
        self.assertEqual(provider.execute_count, 1)


if __name__ == "__main__":
    unittest.main()
