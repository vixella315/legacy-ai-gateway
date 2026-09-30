# Protocol

## Status

Protocol design document only. It is not yet implemented or verified.

## Design goals

The protocol should be:

- small;
- readable;
- versioned;
- extensible;
- recoverable;
- provider-neutral;
- suitable for constrained devices;
- tolerant of unreliable networking;
- duplicate-aware;
- testable without real AI.

## Initial message subset

The first implementation will begin with:

- HELLO
- AUTH
- REQUEST
- RESPONSE
- ERROR

The broader planned protocol also includes capability negotiation, status, chunking, acknowledgement, continuation, cancellation, and keepalive messages.

## Envelope

The planned envelope contains:

- protocol_version
- message_type
- message_id
- session_id
- request_id
- timestamp_or_sequence
- payload

A message ID identifies an individual protocol message. A request ID identifies the logical operation across retries or reconnections.

## Core rule

A network retry is not automatically a new AI request.

Exact wire encoding and transport are intentionally left for implementation and testing.
