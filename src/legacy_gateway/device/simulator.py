"""Deterministic simulated constrained device for Prototype 1.

Step 12.7 models the device side without requiring Nokia/J2ME hardware.
It creates protocol-level requests, tracks a small local inbox/outbox, and
accepts responses from a gateway handler supplied by the caller.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from legacy_gateway.protocol.messages import RequestMessage, ResponseMessage
from legacy_gateway.protocol.validation import validate_request, validate_response


@dataclass(frozen=True)
class DeviceProfile:
    """Capabilities and artificial constraints for the simulated device."""

    device_id: str
    capabilities: tuple[str, ...] = ("TEXT_INPUT", "TEXT_OUTPUT")
    max_request_chars: int = 4096
    max_response_chars: int = 4096
    max_inbox_messages: int = 8

    def __post_init__(self) -> None:
        if not self.device_id.strip():
            raise ValueError("device_id must be non-empty")
        if self.max_request_chars <= 0:
            raise ValueError("max_request_chars must be positive")
        if self.max_response_chars <= 0:
            raise ValueError("max_response_chars must be positive")
        if self.max_inbox_messages <= 0:
            raise ValueError("max_inbox_messages must be positive")


@dataclass
class SimulatedDevice:
    """Small deterministic device-side protocol client."""

    profile: DeviceProfile
    session_id: str = "SIM-SESSION-001"
    _sequence: int = 0
    outbox: list[RequestMessage] = field(default_factory=list)
    inbox: list[ResponseMessage] = field(default_factory=list)

    def create_request(
        self,
        *,
        operation: str,
        request_id: str,
        model: str | None = None,
        content: str = "",
    ) -> RequestMessage:
        """Create and validate a constrained-device request."""
        if len(content) > self.profile.max_request_chars:
            raise ValueError("request content exceeds simulated device limit")

        self._sequence += 1
        request = RequestMessage(
            request_id=request_id,
            session_id=self.session_id,
            device_id=self.profile.device_id,
            operation=operation,
            model=model,
            messages=(
                {"role": "user", "content": content},
            ) if content else (),
            metadata={"device_sequence": self._sequence},
        )
        validate_request(request)
        self.outbox.append(request)
        return request

    def send(
        self,
        request: RequestMessage,
        gateway_handler: Callable[[RequestMessage], ResponseMessage],
    ) -> ResponseMessage:
        """Send one request through a supplied gateway handler."""
        validate_request(request)
        response = gateway_handler(request)
        self.receive(response)
        return response

    def receive(self, response: ResponseMessage) -> None:
        """Validate and store one gateway response."""
        validate_response(response)
        if response.request_id not in {r.request_id for r in self.outbox}:
            raise ValueError("response belongs to an unknown device request")

        if len(response.content) > self.profile.max_response_chars:
            raise ValueError("response exceeds simulated device limit")

        if len(self.inbox) >= self.profile.max_inbox_messages:
            raise OverflowError("simulated device inbox is full")

        self.inbox.append(response)

    def last_response(self) -> ResponseMessage | None:
        """Return the newest received response, if any."""
        return self.inbox[-1] if self.inbox else None
