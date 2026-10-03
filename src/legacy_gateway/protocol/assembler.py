"""Response chunk assembly for constrained-device delivery."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from legacy_gateway.protocol.chunks import ResponseChunk
from legacy_gateway.protocol.messages import RequestStatus, ResponseMessage


@dataclass
class ChunkAssembler:
    _buffers: dict[str, dict[int, str]] = field(default_factory=dict)
    _totals: dict[str, int] = field(default_factory=dict)
    _metadata: dict[str, dict[str, Any]] = field(default_factory=dict)
    _completed: dict[str, tuple[int, dict[int, str], ResponseMessage]] = field(
        default_factory=dict
    )

    def add(self, chunk: ResponseChunk) -> ResponseMessage | None:
        if not chunk.request_id or chunk.total < 1:
            raise ValueError("invalid chunk metadata")
        if chunk.sequence < 1 or chunk.sequence > chunk.total:
            raise ValueError("chunk sequence is outside total")

        completed = self._completed.get(chunk.request_id)
        if completed is not None:
            completed_total, completed_parts, response = completed
            if chunk.total != completed_total:
                raise ValueError("chunk total changed after assembly")
            if completed_parts.get(chunk.sequence) != chunk.content:
                raise ValueError("chunk content changed after assembly")
            if chunk.sequence == 1 and chunk.metadata:
                expected = self._metadata.get(chunk.request_id, {})
                if chunk.metadata != expected:
                    raise ValueError("chunk metadata changed after assembly")
            return response

        known_total = self._totals.get(chunk.request_id)
        if known_total is not None and known_total != chunk.total:
            raise ValueError("chunk total changed during assembly")

        if chunk.metadata:
            known_metadata = self._metadata.get(chunk.request_id)
            if known_metadata is not None and known_metadata != chunk.metadata:
                raise ValueError("chunk metadata changed during assembly")
            self._metadata[chunk.request_id] = dict(chunk.metadata)

        self._totals[chunk.request_id] = chunk.total
        parts = self._buffers.setdefault(chunk.request_id, {})

        if chunk.sequence in parts and parts[chunk.sequence] != chunk.content:
            raise ValueError("chunk content changed during assembly")
        parts[chunk.sequence] = chunk.content

        if len(parts) != chunk.total:
            return None

        content = "".join(parts[i] for i in range(1, chunk.total + 1))
        metadata = self._metadata.get(chunk.request_id, {})
        status_value = metadata.get("status", RequestStatus.SUCCESS.value)
        try:
            status = RequestStatus(status_value)
        except ValueError as exc:
            raise ValueError("invalid response status in chunk metadata") from exc

        response = ResponseMessage(
            request_id=chunk.request_id,
            status=status,
            content=content,
            chunks=metadata.get("chunks", ()),
            usage=metadata.get("usage", {}),
            provider=metadata.get("provider"),
            model=metadata.get("model"),
            finish_reason=metadata.get("finish_reason"),
            error=metadata.get("error"),
        )

        completed_parts = dict(parts)
        self._completed[chunk.request_id] = (
            chunk.total,
            completed_parts,
            response,
        )
        del self._buffers[chunk.request_id]
        del self._totals[chunk.request_id]
        self._metadata.pop(chunk.request_id, None)
        return response
