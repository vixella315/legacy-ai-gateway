"""Tests for Step 12.10 response chunking."""

import unittest

from legacy_gateway.protocol.assembler import ChunkAssembler
from legacy_gateway.protocol.chunks import chunk_response
from legacy_gateway.protocol.messages import RequestStatus, ResponseMessage


class ResponseChunkingTests(unittest.TestCase):
    def response(self):
        return ResponseMessage(
            request_id="R-12-10",
            status=RequestStatus.SUCCESS,
            content="ABCDEFGHIJ",
        )

    def test_large_response_is_split_into_ordered_chunks(self):
        chunks = chunk_response(self.response(), 4)
        self.assertEqual(
            [(c.sequence, c.total, c.content) for c in chunks],
            [(1, 3, "ABCD"), (2, 3, "EFGH"), (3, 3, "IJ")],
        )

    def test_chunks_reassemble_in_order(self):
        assembler = ChunkAssembler()
        result = None
        for chunk in chunk_response(self.response(), 4):
            result = assembler.add(chunk)
        self.assertEqual(result.content, "ABCDEFGHIJ")
        self.assertEqual(result.request_id, "R-12-10")

    def test_missing_chunk_keeps_response_incomplete(self):
        assembler = ChunkAssembler()
        chunks = chunk_response(self.response(), 4)
        self.assertIsNone(assembler.add(chunks[0]))
        self.assertIsNone(assembler.add(chunks[2]))

    def test_out_of_order_chunks_reassemble_by_sequence(self):
        assembler = ChunkAssembler()
        chunks = chunk_response(self.response(), 4)
        result = assembler.add(chunks[2])
        self.assertIsNone(result)
        assembler.add(chunks[0])
        result = assembler.add(chunks[1])
        self.assertEqual(result.content, "ABCDEFGHIJ")

    def test_duplicate_chunk_does_not_duplicate_content(self):
        assembler = ChunkAssembler()
        chunks = chunk_response(self.response(), 4)
        assembler.add(chunks[0])
        assembler.add(chunks[0])
        assembler.add(chunks[1])
        result = assembler.add(chunks[2])
        self.assertEqual(result.content, "ABCDEFGHIJ")

    def test_invalid_chunk_size_is_rejected(self):
        with self.assertRaises(ValueError):
            chunk_response(self.response(), 0)

    def test_changed_total_is_rejected(self):
        assembler = ChunkAssembler()
        chunks = chunk_response(self.response(), 4)
        assembler.add(chunks[0])
        changed = type(chunks[0])(
            request_id=chunks[0].request_id,
            sequence=1,
            total=99,
            content=chunks[0].content,
        )
        with self.assertRaises(ValueError):
            assembler.add(changed)


if __name__ == "__main__":
    unittest.main()
