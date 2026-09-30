"""Deterministic constrained-device simulator for Prototype 1.

The simulator models only the device-side responsibilities: capabilities,
request creation, response reception, and a small bounded local history.
It does not perform AI inference or network transport.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from legacy_gateway.protocol.messages import RequestMessage, ResponseMessage
from legacy_gateway.protocol.validation import validate_request, validate_response


@dataclass(frozen=True)
class DeviceProfile:
    """Explicit constraints used by the simulated device."""

    device_id: str
    max_request_chars: int = 4096
    max_response_chars: int = 8192
    capabilities: tuple[str, ...] = ("chat",)


@dataclass
class SimulatedDevice:
    """Minimal device-side participant for Prototype 1."""

    profile: DeviceProfile
    session_id: str = "SIM-SESSION-1"
    _request_sequence: int = 0
    last_response: ResponseMessage | None = None
    response_history: list[ResponseMessage] = field(default_factory=list)

    def hello(self) -> dict[str, Any]:
        """Return the device capability description."""
        return {
            "device_id": self.profile.device_id,
            "capabilities": self.profile.capabilities,
        }

    def create_request(
        self,
        operation: str,
        *,
        model: str | None = "mock-model",
        content: str = "",
    ) -> RequestMessage:
        """Create and validate one logical request within device limits."""
        if len(content) > self.profile.max_request_chars:
            raise ValueError("request content exceeds simulated device limit")

        self._request_sequence += 1
        request = RequestMessage(
            request_id=f"{self.profile.device_id}-R-{self._request_sequence}",
            session_id=self.session_id,
            device_id=self.profile.device_id,
            operation=operation,
            messages=({"role": "user", "content": content},),
            model=model,
        )
        validate_request(request)
        return request

    def receive_response(self, response: ResponseMessage) -> None:
        """Validate and store a gateway response within device limits."""
        validate_response(response)
        if len(response.content) > self.profile.max_response_chars:
            raise ValueError("response exceeds simulated device limit")
        self.last_response = response
        self.response_history.append(response)
