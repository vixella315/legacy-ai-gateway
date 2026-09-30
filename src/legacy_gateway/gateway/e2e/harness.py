"""In-process end-to-end harness for Prototype 1.

This is deliberately not a network transport. It connects the existing
simulated device, gateway, and mock provider so the complete logical path can
be tested before transport is introduced.
"""

from __future__ import annotations

from dataclasses import dataclass

from legacy_gateway.device import SimulatedDevice
from legacy_gateway.gateway import Gateway
from legacy_gateway.protocol.messages import ResponseMessage
from legacy_gateway.providers import MockProvider


@dataclass
class EndToEndHarness:
    """Connect one simulated device to one gateway."""

    device: SimulatedDevice
    gateway: Gateway

    @classmethod
    def with_mock_provider(
        cls,
        device: SimulatedDevice,
        provider: MockProvider | None = None,
    ) -> "EndToEndHarness":
        return cls(device=device, gateway=Gateway(provider or MockProvider()))

    def send_chat(self, content: str) -> ResponseMessage:
        request = self.device.create_request("chat", content=content)
        response = self.gateway.handle_request(request)
        self.device.receive_response(response)
        return response
