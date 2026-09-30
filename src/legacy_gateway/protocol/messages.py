"""Protocol data objects for the Legacy AI Gateway.

Step 12.2 defines data structures only. Validation belongs to Step 12.3.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MessageType(str, Enum):
    """Initial protocol message types."""

    HELLO = "HELLO"
    AUTH = "AUTH"
    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE"
    ERROR = "ERROR"


class RequestStatus(str, Enum):
    """Canonical request outcome states used by protocol responses."""

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    UNCERTAIN = "UNCERTAIN"


@dataclass(frozen=True)
class ProtocolEnvelope:
    """Common envelope shared by protocol messages."""

    protocol_version: str
    message_type: MessageType
    message_id: str
    session_id: str | None = None
    request_id: str | None = None
    timestamp_or_sequence: str | int | None = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class HelloMessage:
    """Device/gateway protocol introduction."""

    device_id: str
    capabilities: tuple[str, ...] = ()


@dataclass(frozen=True)
class AuthMessage:
    """Authentication material exchanged after HELLO."""

    credential: str


@dataclass(frozen=True)
class RequestMessage:
    """Canonical logical request sent through the gateway."""

    request_id: str
    session_id: str
    device_id: str
    operation: str
    messages: tuple[dict[str, Any], ...] = ()
    model: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    tools: tuple[dict[str, Any], ...] = ()
    limits: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ResponseMessage:
    """Canonical response returned by the gateway."""

    request_id: str
    status: RequestStatus
    content: str = ""
    chunks: tuple[dict[str, Any], ...] = ()
    usage: dict[str, Any] = field(default_factory=dict)
    provider: str | None = None
    model: str | None = None
    finish_reason: str | None = None
    error: dict[str, Any] | None = None


@dataclass(frozen=True)
class ErrorMessage:
    """Canonical protocol error."""

    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)
