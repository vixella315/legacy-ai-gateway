"""Tests for Step 12.7 simulated device."""

import unittest

from legacy_gateway.device import DeviceProfile, SimulatedDevice
from legacy_gateway.protocol.messages import RequestStatus, ResponseMessage


class SimulatedDeviceTests(unittest.TestCase):
    def make_device(self) -> SimulatedDevice:
        return SimulatedDevice(
            DeviceProfile(
                device_id="SIM-001",
                max_request_chars=16,
                max_response_chars=32,
            )
        )

    def test_hello_reports_device_identity_and_capabilities(self) -> None:
        device = self.make_device()
        self.assertEqual(
            device.hello(),
            {"device_id": "SIM-001", "capabilities": ("chat",)},
        )

    def test_create_request_generates_unique_logical_ids(self) -> None:
        device = self.make_device()
        first = device.create_request("chat", content="hello")
        second = device.create_request("chat", content="again")
        self.assertEqual(first.device_id, "SIM-001")
        self.assertEqual(first.session_id, "SIM-SESSION-1")
        self.assertEqual(first.request_id, "SIM-001-R-1")
        self.assertEqual(second.request_id, "SIM-001-R-2")

    def test_request_limit_is_enforced_locally(self) -> None:
        device = self.make_device()
        with self.assertRaises(ValueError):
            device.create_request("chat", content="12345678901234567")

    def test_receive_response_validates_and_stores(self) -> None:
        device = self.make_device()
        response = ResponseMessage(
            request_id="SIM-001-R-1",
            status=RequestStatus.SUCCESS,
            content="hello",
            provider="mock",
            model="mock-model",
        )
        device.receive_response(response)
        self.assertIs(device.last_response, response)
        self.assertEqual(device.response_history, [response])

    def test_response_limit_is_enforced_locally(self) -> None:
        device = self.make_device()
        response = ResponseMessage(
            request_id="SIM-001-R-1",
            status=RequestStatus.SUCCESS,
            content="123456789012345678901234567890123",
        )
        with self.assertRaises(ValueError):
            device.receive_response(response)
        self.assertIsNone(device.last_response)

    def test_malformed_response_is_rejected(self) -> None:
        device = self.make_device()
        with self.assertRaises(ValueError):
            device.receive_response(
                ResponseMessage(
                    request_id="",
                    status=RequestStatus.SUCCESS,
                    content="hello",
                )
            )


if __name__ == "__main__":
    unittest.main()
