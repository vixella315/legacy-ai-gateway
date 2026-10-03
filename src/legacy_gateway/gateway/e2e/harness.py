"""In-process end-to-end harness for Prototype 1.

This is deliberately not a network transport. It connects the existing
simulated device, gateway, and mock provider so the logical path can be tested
before transport is introduced.

Step 12.9 adds delivery-failure simulation. Recovery re-delivers an already
produced response; it does not re-execute the provider operation.

Step 12.10 integrates response chunking at the simulated-device delivery
boundary. Chunking is transport behavior: the device still enforces its
complete-response storage limit after reassembly.
"""

from __future__ import annotations

from dataclasses import dataclass

from legacy_gateway.device import SimulatedDevice
from legacy_gateway.gateway import Gateway
from legacy_gateway.protocol.chunks import chunk_response
from legacy_gateway.protocol.messages import (
    RequestMessage,
    RequestStatus,
    ResponseMessage,
)
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
        """Deliver an already-created response, chunking large success content."""
        if (
            response.status is RequestStatus.SUCCESS
            and len(response.content) > self.device.profile.response_chunk_size
        ):
            for chunk in chunk_response(
                response, self.device.profile.response_chunk_size
            ):
                self.device.receive_response_chunk(chunk)
            return
        self.device.receive_response(response)

    def send_chat(self, content: str) -> ResponseMessage:
        request = self.create_request(content)
        response = self.execute(request)
        self.deliver(response)
        return response

    def recover_delivery(self, response: ResponseMessage) -> None:
        """Recover a lost delivery without re-running the provider."""
        self.deliver(response)
