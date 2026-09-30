"""Response chunking helpers for constrained-device delivery."""

from __future__ import annotations

from dataclasses import dataclass

from legacy_gateway.protocol.messages import ResponseMessage


@dataclass(frozen=True)
class ResponseChunk:
    request_id: str
    sequence: int
    total: int
    content: str


def chunk_response(response: ResponseMessage, chunk_size: int) -> list[ResponseChunk]:
    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")
    text = response.content
    total = max(1, (len(text) + chunk_size - 1) // chunk_size)
    return [
        ResponseChunk(
            request_id=response.request_id,
            sequence=i,
            total=total,
            content=text[(i - 1) * chunk_size : i * chunk_size],
        )
        for i in range(1, total + 1)
    ]
