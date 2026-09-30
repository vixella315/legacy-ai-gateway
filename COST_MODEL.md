# Cost Model

## Status

Cost-control design only. No paid provider is enabled.

## Operating modes

- MOCK — default prototype mode
- LOCAL — future local-model mode
- PAID — future commercial-provider mode

Paid AI is OFF by default.

## Cost-control principle

The system must be useful without spending money, and paid resources must never be used accidentally.

## Planned controls

Requests will eventually carry cost/resource identity including:

- request ID;
- device ID;
- provider;
- model;
- operation;
- estimated cost;
- reserved cost;
- actual cost;
- resource units;
- timestamp.

Planned budgets include global, device, provider, model, and operation limits.

No silent provider switching, model upgrades, or spending increases are permitted by design.

Exact budgets and pricing mechanisms will be selected and tested later.
