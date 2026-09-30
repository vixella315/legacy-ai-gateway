# Architecture

## Status

Design document only. The architecture described here is not yet implemented or verified.

## Core architecture

```
DEVICE
  ↓
DEVICE PROTOCOL
  ↓
AI GATEWAY
  ↓
PROVIDER ADAPTER
  ↓
AI MODEL / LOCAL MODEL
  ↓
TOOLS
  ↓
GATEWAY
  ↓
DEVICE
```

The gateway is intended to be reusable. A Nokia or other legacy device is a client/prototype, not the definition of the gateway.

## Planes

1. Device plane
2. Protocol plane
3. Gateway plane
4. Provider/local-model plane
5. Tool/service adapter plane

Human authorization remains above sensitive, costly, or irreversible external actions.

## Prototype 1 boundary

Prototype 1 uses:

```
Simulated Device → Protocol → Gateway → Mock Provider
```

Real providers, local AI, J2ME, physical hardware, and legacy network compatibility are later stages.
