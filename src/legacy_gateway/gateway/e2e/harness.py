"""In-process end-to-end harness for Prototype 1.

This is deliberately not a network transport. It connects the existing
simulated device, gateway, and mock provider so the logical path can be tested
before transport is introduced.

Step 12.9 adds delivery-failure simulation. Recovery re-delivers an already
produced response; it does not re-execute the provider operation.
"""

from __future__ import annotations

from dataclasses import dataclass

from legacy_gateway.device import SimulatedDevice
from legacy_gateway.gateway import Gateway
from legacy_gateway.protocol.messages import RequestMessage, ResponseMessage
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

    def create_request(self, content: str) -> RequestMessage:
        return self.device.create_request("chat", content=content)

    def execute(self, request: RequestMessage) -> ResponseMessage:
        """Execute exactly one gateway/provider operation."""
        return self.gateway.handle_request(request)

    def deliver(self, response: ResponseMessage) -> None:
        """Deliver an already-created response to the device."""
        self.device.receive_response(response)

    def send_chat(self, content: str) -> ResponseMessage:
        request = self.create_request(content)
        response = self.execute(request)
        self.deliver(response)
        return response

    def recover_delivery(self, response: ResponseMessage) -> None:
        """Recover a lost delivery without re-running the provider."""
        self.deliver(response)
