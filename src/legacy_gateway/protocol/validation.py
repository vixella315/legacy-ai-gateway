"""Validation helpers for the Legacy AI Gateway protocol.

Step 12.3 validates the structural invariants of protocol data objects.
Transport, serialization, authentication, and gateway policy remain outside
this module.
"""

from __future__ import annotations

from typing import Any

from .messages import (
    AuthMessage,
    ErrorMessage,
    HelloMessage,
    MessageType,
    ProtocolEnvelope,
    RequestMessage,
    RequestStatus,
    ResponseMessage,
)

SUPPORTED_PROTOCOL_VERSION = "1"


class ProtocolValidationError(ValueError):
    """Raised when a protocol object violates a structural invariant."""


def _require_non_empty(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ProtocolValidationError(f"{field_name} must be a non-empty string")


def validate_envelope(envelope: ProtocolEnvelope) -> None:
    """Validate required envelope fields."""
    if not isinstance(envelope, ProtocolEnvelope):
        raise ProtocolValidationError("envelope must be a ProtocolEnvelope")
    _require_non_empty(envelope.protocol_version, "protocol_version")
    if envelope.protocol_version != SUPPORTED_PROTOCOL_VERSION:
        raise ProtocolValidationError(
            f"unsupported protocol_version: {envelope.protocol_version}"
        )
    if not isinstance(envelope.message_type, MessageType):
        raise ProtocolValidationError("message_type must be a MessageType")
    _require_non_empty(envelope.message_id, "message_id")
    if envelope.session_id is not None and not isinstance(envelope.session_id, str):
        raise ProtocolValidationError("session_id must be a string or None")
    if envelope.request_id is not None and not isinstance(envelope.request_id, str):
        raise ProtocolValidationError("request_id must be a string or None")
    if envelope.timestamp_or_sequence is not None and not isinstance(
        envelope.timestamp_or_sequence, (str, int)
    ):
        raise ProtocolValidationError(
            "timestamp_or_sequence must be a string, integer, or None"
        )
    if not isinstance(envelope.payload, dict):
        raise ProtocolValidationError("payload must be a dictionary")


def validate_hello(message: HelloMessage) -> None:
    """Validate a HELLO message."""
    if not isinstance(message, HelloMessage):
        raise ProtocolValidationError("message must be a HelloMessage")
    _require_non_empty(message.device_id, "device_id")
    if not isinstance(message.capabilities, tuple):
        raise ProtocolValidationError("capabilities must be a tuple")


def validate_auth(message: AuthMessage) -> None:
    """Validate an AUTH message."""
    if not isinstance(message, AuthMessage):
        raise ProtocolValidationError("message must be an AuthMessage")
    _require_non_empty(message.credential, "credential")


def validate_request(message: RequestMessage) -> None:
    """Validate a canonical request."""
    if not isinstance(message, RequestMessage):
        raise ProtocolValidationError("message must be a RequestMessage")
    _require_non_empty(message.request_id, "request_id")
    _require_non_empty(message.session_id, "session_id")
    _require_non_empty(message.device_id, "device_id")
    _require_non_empty(message.operation, "operation")
    if not isinstance(message.messages, tuple):
        raise ProtocolValidationError("messages must be a tuple")
    if not isinstance(message.parameters, dict):
        raise ProtocolValidationError("parameters must be a dictionary")
    if not isinstance(message.tools, tuple):
        raise ProtocolValidationError("tools must be a tuple")
    if not isinstance(message.limits, dict):
        raise ProtocolValidationError("limits must be a dictionary")
    if not isinstance(message.metadata, dict):
        raise ProtocolValidationError("metadata must be a dictionary")


def validate_response(message: ResponseMessage) -> None:
    """Validate a canonical response."""
    if not isinstance(message, ResponseMessage):
        raise ProtocolValidationError("message must be a ResponseMessage")
    _require_non_empty(message.request_id, "request_id")
    if not isinstance(message.status, RequestStatus):
        raise ProtocolValidationError("status must be a RequestStatus")
    if not isinstance(message.content, str):
        raise ProtocolValidationError("content must be a string")
    if not isinstance(message.chunks, tuple):
        raise ProtocolValidationError("chunks must be a tuple")
    if not isinstance(message.usage, dict):
        raise ProtocolValidationError("usage must be a dictionary")
    if message.provider is not None and not isinstance(message.provider, str):
        raise ProtocolValidationError("provider must be a string or None")
    if message.model is not None and not isinstance(message.model, str):
        raise ProtocolValidationError("model must be a string or None")
    if message.finish_reason is not None and not isinstance(
        message.finish_reason, str
    ):
        raise ProtocolValidationError("finish_reason must be a string or None")
    if message.error is not None and not isinstance(message.error, dict):
        raise ProtocolValidationError("error must be a dictionary or None")


def validate_error(message: ErrorMessage) -> None:
    """Validate a canonical protocol error."""
    if not isinstance(message, ErrorMessage):
        raise ProtocolValidationError("message must be an ErrorMessage")
    _require_non_empty(message.code, "code")
    _require_non_empty(message.message, "message")
    if not isinstance(message.details, dict):
        raise ProtocolValidationError("details must be a dictionary")


def validate_message(message: Any) -> None:
    """Dispatch validation to the appropriate protocol data-object validator."""
    validators = (
        (ProtocolEnvelope, validate_envelope),
        (HelloMessage, validate_hello),
        (AuthMessage, validate_auth),
        (RequestMessage, validate_request),
        (ResponseMessage, validate_response),
        (ErrorMessage, validate_error),
    )
    for message_type, validator in validators:
        if isinstance(message, message_type):
            validator(message)
            return
    raise ProtocolValidationError(
        f"unsupported protocol object type: {type(message).__name__}"
    )


__all__ = [
    "ProtocolValidationError",
    "SUPPORTED_PROTOCOL_VERSION",
    "validate_auth",
    "validate_envelope",
    "validate_error",
    "validate_hello",
    "validate_message",
    "validate_request",
    "validate_response",
]
