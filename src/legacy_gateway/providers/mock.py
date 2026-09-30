"""Deterministic mock provider for Step 12.4.

The mock provider never calls an external service and never incurs an AI
provider charge. Its modes deliberately exercise normal, slow, partial,
duplicate, malformed, rate-limit, and uncertain paths.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Any

from legacy_gateway.protocol.messages import RequestMessage, RequestStatus, ResponseMessage

from .interface import (
    ProviderError,
    ProviderIdentity,
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnavailable,
    ProviderUnknownOutcome,
)


class MockMode(str, Enum):
    SUCCESS = "MOCK_SUCCESS"
    FAILURE = "MOCK_FAILURE"
    TIMEOUT = "MOCK_TIMEOUT"
    SLOW = "MOCK_SLOW"
    RATE_LIMIT = "MOCK_RATE_LIMIT"
    PARTIAL = "MOCK_PARTIAL"
    MALFORMED = "MOCK_MALFORMED"
    DUPLICATE = "MOCK_DUPLICATE"
    UNKNOWN = "MOCK_UNKNOWN"


class MockProvider:
    """Deterministic provider used for local and automated tests."""

    def __init__(
        self,
        mode: MockMode = MockMode.SUCCESS,
        *,
        slow_delay_seconds: float = 0.0,
    ) -> None:
        if slow_delay_seconds < 0:
            raise ValueError("slow_delay_seconds must be non-negative")
        self.mode = mode
        self.slow_delay_seconds = slow_delay_seconds
        self.execute_count = 0

    def identity(self) -> ProviderIdentity:
        return ProviderIdentity(name="mock", version="1")

    def execute(self, request: RequestMessage) -> ResponseMessage | Any:
        self.execute_count += 1

        if self.mode is MockMode.FAILURE:
            raise ProviderError("mock provider failure")
        if self.mode is MockMode.TIMEOUT:
            raise ProviderTimeout("mock provider timeout")
        if self.mode is MockMode.SLOW and self.slow_delay_seconds:
            time.sleep(self.slow_delay_seconds)
        if self.mode is MockMode.RATE_LIMIT:
            raise ProviderRateLimited("mock provider rate limited")
        if self.mode is MockMode.UNKNOWN:
            raise ProviderUnknownOutcome("mock provider outcome is unknown")
        if self.mode is MockMode.MALFORMED:
            return {"request_id": request.request_id, "status": "NOT_A_VALID_RESPONSE"}

        if self.mode is MockMode.PARTIAL:
            return ResponseMessage(
                request_id=request.request_id,
                status=RequestStatus.SUCCESS,
                content="",
                chunks=(
                    {"sequence": 1, "content": "MOCK_PART_1"},
                    {"sequence": 2, "content": "MOCK_PART_2"},
                ),
                provider="mock",
                model=request.model,
                finish_reason="mock_partial",
            )

        if self.mode is MockMode.DUPLICATE:
            return ResponseMessage(
                request_id=request.request_id,
                status=RequestStatus.SUCCESS,
                content="MOCK_DUPLICATE_RESPONSE",
                provider="mock",
                model=request.model,
                finish_reason="mock_duplicate",
            )

        return ResponseMessage(
            request_id=request.request_id,
            status=RequestStatus.SUCCESS,
            content=f"MOCK_RESPONSE:{request.operation}",
            provider="mock",
            model=request.model,
            finish_reason="mock_complete",
        )
