# Security

## Status

Security design only. This document does not constitute a security audit or proof of security.

## Core principle

The legacy device may be limited. It must not be the place where the system's most important secrets live.

## Planned principles

- Provider master/API credentials remain at the gateway.
- Secrets must not be committed to source.
- Secrets must not appear in ordinary logs.
- Authentication and authorization are separate concerns.
- Devices must be individually revocable.
- Requests must be uniquely identifiable.
- Paid operations must be duplicate-aware.
- Legacy compatibility should be isolated at the device edge.
- External web/tool content is untrusted input.
- Tools require explicit gateway authorization.
- Sensitive or irreversible actions require human authorization.
- Security assumptions must be tested.
- Emulator behavior is not proof of hardware security.

Exact authentication, credential format, certificate design, pairing flow, expiration, rate limits, and legacy transport security remain implementation decisions.
