"""Provider interface for the Legacy AI Gateway.

Step 12.4 establishes the provider contract needed by the deterministic mock.
Real provider adapters belong to later steps.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from legacy_gateway.protocol.messages import RequestMessage, ResponseMessage


class ProviderError(RuntimeError):
    """Base exception for provider execution failures."""


class ProviderTimeout(ProviderError):
    """Provider deliberately or unexpectedly timed out."""


class ProviderUnavailable(ProviderError):
    """Provider is unavailable."""


class ProviderRateLimited(ProviderError):
    """Provider deliberately returned a rate-limit condition."""


class ProviderUnknownOutcome(ProviderError):
    """Provider outcome cannot safely be classified as success or failure."""


@dataclass(frozen=True)
class ProviderIdentity:
    name: str
    version: str


class ProviderAdapter(Protocol):
    """Minimal provider adapter contract."""

    def identity(self) -> ProviderIdentity:
        ...

    def execute(self, request: RequestMessage) -> ResponseMessage:
        ...
