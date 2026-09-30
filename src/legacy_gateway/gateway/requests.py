"""Request lifecycle state for the Legacy AI Gateway.

Step 12.6 tracks a logical request independently from provider execution.
Persistence, recovery, retries, and cost accounting belong to later steps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from legacy_gateway.protocol.messages import RequestMessage


class RequestLifecycle(str, Enum):
    NEW = "NEW"
    RECEIVED = "RECEIVED"
    AUTHORIZED = "AUTHORIZED"
    COST_CHECKED = "COST_CHECKED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    UNCERTAIN = "UNCERTAIN"


class InvalidRequestTransition(ValueError):
    """Raised when a request attempts an illegal lifecycle transition."""


_TERMINAL_STATES = {
    RequestLifecycle.SUCCESS,
    RequestLifecycle.FAILURE,
    RequestLifecycle.UNCERTAIN,
}

_ALLOWED_TRANSITIONS = {
    RequestLifecycle.NEW: {RequestLifecycle.RECEIVED},
    RequestLifecycle.RECEIVED: {RequestLifecycle.AUTHORIZED},
    RequestLifecycle.AUTHORIZED: {RequestLifecycle.COST_CHECKED},
    RequestLifecycle.COST_CHECKED: {RequestLifecycle.RUNNING},
    RequestLifecycle.RUNNING: {
        RequestLifecycle.SUCCESS,
        RequestLifecycle.FAILURE,
        RequestLifecycle.UNCERTAIN,
    },
    RequestLifecycle.SUCCESS: set(),
    RequestLifecycle.FAILURE: set(),
    RequestLifecycle.UNCERTAIN: set(),
}


@dataclass
class RequestRecord:
    """In-memory lifecycle record for one logical request."""

    request_id: str
    device_id: str
    session_id: str
    state: RequestLifecycle = RequestLifecycle.NEW
    history: list[RequestLifecycle] = field(
        default_factory=lambda: [RequestLifecycle.NEW]
    )

    @classmethod
    def from_request(cls, request: RequestMessage) -> "RequestRecord":
        return cls(
            request_id=request.request_id,
            device_id=request.device_id,
            session_id=request.session_id,
        )

    @property
    def terminal(self) -> bool:
        return self.state in _TERMINAL_STATES

    def transition(self, new_state: RequestLifecycle) -> RequestLifecycle:
        if new_state not in _ALLOWED_TRANSITIONS[self.state]:
            raise InvalidRequestTransition(
                f"invalid request transition: {self.state.value} -> {new_state.value}"
            )
        self.state = new_state
        self.history.append(new_state)
        return self.state

    def can_transition_to(self, new_state: RequestLifecycle) -> bool:
        return new_state in _ALLOWED_TRANSITIONS[self.state]


class RequestTracker:
    """In-memory collection of logical request records."""

    def __init__(self) -> None:
        self._records: dict[str, RequestRecord] = {}

    def create(self, request: RequestMessage) -> RequestRecord:
        if request.request_id in self._records:
            raise ValueError(f"request already exists: {request.request_id}")
        record = RequestRecord.from_request(request)
        self._records[request.request_id] = record
        return record

    def get(self, request_id: str) -> RequestRecord | None:
        return self._records.get(request_id)

    def require(self, request_id: str) -> RequestRecord:
        record = self.get(request_id)
        if record is None:
            raise KeyError(f"unknown request: {request_id}")
        return record

    def transition(
        self, request_id: str, new_state: RequestLifecycle
    ) -> RequestRecord:
        record = self.require(request_id)
        record.transition(new_state)
        return record

    def __len__(self) -> int:
        return len(self._records)
