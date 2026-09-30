# Threat Model

## Status

Threat-model baseline only. It is not a completed security assessment.

## Assets

- provider credentials;
- device credentials;
- user data;
- request history;
- cost/account information;
- tool credentials;
- durable request state.

## Threat categories

- stolen device;
- stolen device credential;
- replay;
- provider credential leakage;
- sensitive logs;
- man-in-the-middle;
- fake gateway;
- malicious client;
- protocol abuse;
- duplicate paid requests;
- prompt injection through external content;
- unauthorized tool use;
- provider compromise;
- gateway compromise;
- database or backup theft;
- dependency compromise;
- malicious update.

## Planned controls

Controls will be implemented incrementally and verified through the testing strategy. No threat is considered mitigated merely because a control is documented here.
