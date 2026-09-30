# Testing

## Authoritative test command

From the repository root:

    python scripts/test.py

The runner uses Python's standard-library unittest framework and adds the
repository's src/ directory to the import path. No third-party test runner
is required.

## Discovery

The command recursively discovers files matching:

    tests/**/test_*.py

The test directories are Python packages so discovery is deterministic across
supported environments.

## Pass criteria

A test run succeeds only when every discovered test passes, the process exits
with status 0, and there are no discovery or import errors.

A passing local test run does not by itself prove CI or physical-hardware
compatibility.

## Current scope

The suite covers protocol validation, gateway core, request state, end-to-end
logical communication, failure/recovery, and response chunking.

Paid providers, real networking, J2ME, Nokia hardware, and physical-device
qualification remain outside the current scope.
