"""Response chunk assembly for constrained-device delivery."""

from __future__ import annotations

from dataclasses import dataclass, field

from legacy_gateway.protocol.chunks import ResponseChunk
from legacy_gateway.protocol.messages import RequestStatus, ResponseMessage


@dataclass
class ChunkAssembler:
    _buffers: dict[str, dict[int, str]] = field(default_factory=dict)
    _totals: dict[str, int] = field(default_factory=dict)

    def add(self, chunk: ResponseChunk) -> ResponseMessage | None:
        if not chunk.request_id or chunk.total < 1:
            raise ValueError("invalid chunk metadata")
        if chunk.sequence < 1 or chunk.sequence > chunk.total:
            raise ValueError("chunk sequence is outside total")
        known_total = self._totals.get(chunk.request_id)
        if known_total is not None and known_total != chunk.total:
            raise ValueError("chunk total changed during assembly")
        self._totals[chunk.request_id] = chunk.total
        parts = self._buffers.setdefault(chunk.request_id, {})
        parts[chunk.sequence] = chunk.content
        if len(parts) != chunk.total:
            return None
        content = "".join(parts[i] for i in range(1, chunk.total + 1))
        response = ResponseMessage(
            request_id=chunk.request_id,
            status=RequestStatus.SUCCESS,
            content=content,
        )
        del self._buffers[chunk.request_id]
        del self._totals[chunk.request_id]
        return response
