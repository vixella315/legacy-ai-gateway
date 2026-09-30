"""Tests for Step 12.3 protocol validation."""

import unittest

from legacy_gateway.protocol.messages import (
    AuthMessage,
    ErrorMessage,
    HelloMessage,
    MessageType,
    ProtocolEnvelope,
    RequestMessage,
    RequestStatus,
    ResponseMessage,
)
from legacy_gateway.protocol.validation import (
    ProtocolValidationError,
    validate_auth,
    validate_envelope,
    validate_error,
    validate_hello,
    validate_message,
    validate_request,
    validate_response,
)


class ProtocolValidationTests(unittest.TestCase):
    def test_valid_envelope(self) -> None:
        validate_envelope(
            ProtocolEnvelope(
                protocol_version="1",
                message_type=MessageType.HELLO,
                message_id="M-1",
            )
        )

    def test_rejects_unsupported_protocol_version(self) -> None:
        with self.assertRaises(ProtocolValidationError):
            validate_envelope(
                ProtocolEnvelope(
                    protocol_version="99",
                    message_type=MessageType.HELLO,
                    message_id="M-1",
                )
            )

    def test_rejects_empty_message_id(self) -> None:
        with self.assertRaises(ProtocolValidationError):
            validate_envelope(
                ProtocolEnvelope(
                    protocol_version="1",
                    message_type=MessageType.HELLO,
                    message_id=" ",
                )
            )

    def test_valid_hello_and_auth(self) -> None:
        validate_hello(HelloMessage(device_id="D-1", capabilities=("chat",)))
        validate_auth(AuthMessage(credential="device-token"))

    def test_rejects_empty_auth_credential(self) -> None:
        with self.assertRaises(ProtocolValidationError):
            validate_auth(AuthMessage(credential=""))

    def test_valid_request(self) -> None:
        validate_request(
            RequestMessage(
                request_id="R-1",
                session_id="S-1",
                device_id="D-1",
                operation="chat",
            )
        )

    def test_rejects_request_without_required_identity(self) -> None:
        with self.assertRaises(ProtocolValidationError):
            validate_request(
                RequestMessage(
                    request_id="",
                    session_id="S-1",
                    device_id="D-1",
                    operation="chat",
                )
            )

    def test_valid_response_states(self) -> None:
        for status in RequestStatus:
            validate_response(ResponseMessage(request_id="R-1", status=status))

    def test_rejects_invalid_response_status(self) -> None:
        with self.assertRaises(ProtocolValidationError):
            validate_response(
                ResponseMessage(
                    request_id="R-1",
                    status="SUCCESS",  # type: ignore[arg-type]
                )
            )

    def test_valid_error(self) -> None:
        validate_error(ErrorMessage(code="TIMEOUT", message="provider timed out"))

    def test_rejects_empty_error_code(self) -> None:
        with self.assertRaises(ProtocolValidationError):
            validate_error(ErrorMessage(code="", message="invalid"))

    def test_dispatcher_accepts_all_protocol_objects(self) -> None:
        objects = (
            ProtocolEnvelope("1", MessageType.HELLO, "M-1"),
            HelloMessage("D-1"),
            AuthMessage("token"),
            RequestMessage("R-1", "S-1", "D-1", "chat"),
            ResponseMessage("R-1", RequestStatus.SUCCESS),
            ErrorMessage("ERROR", "failure"),
        )
        for obj in objects:
            validate_message(obj)

    def test_dispatcher_rejects_unknown_object(self) -> None:
        with self.assertRaises(ProtocolValidationError):
            validate_message({"message_type": "HELLO"})


if __name__ == "__main__":
    unittest.main()
