# Legacy AI Gateway

## Project

Legacy AI Gateway is an independent engineering project exploring how constrained and legacy devices can act as interfaces to modern AI through a gateway.

The device is the interface/client. Modern AI computation is remote unless a later project stage explicitly qualifies local inference.

## Prototype 1

Prototype 1 is a mock end-to-end system:

```
Simulated Device
      ↓
Device Protocol
      ↓
Gateway
      ↓
Mock Provider
      ↓
Gateway
      ↓
Simulated Device
```

No paid AI provider, Nokia hardware, J2ME runtime, legacy TLS configuration, or local model is part of Prototype 1.

## Current stage

Step 12 — Prototype Implementation

Current substep: 12.1 — Repository Skeleton

The skeleton contains project structure and design documents only. Functionality is not yet implemented.

## Project rules

- This repository is completely separate from all other projects.
- Free-first development is required.
- Paid AI is OFF by default.
- The mock provider is the first provider.
- Do not put provider master credentials on constrained devices.
- Do not treat emulator behavior as proof of physical hardware behavior.
- Do not claim functionality is verified until it has been tested and recorded.
- Preserve evidence, provenance, and reproducibility.

## Evidence status

The project uses an evidence ladder:

0. Not tested / assumption
1. Claim
2. Third-party evidence
3. Our automated test
4. Independently reproduced
5. Physical measurement or test

Public reference projects may inform design, but their results are not automatically our results.

## License

No project license has been selected yet. This repository is not granting an implied open-source license through this README.
