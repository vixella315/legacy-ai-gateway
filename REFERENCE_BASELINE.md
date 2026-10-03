# Upstream Reference Baseline

Reference implementation: AIKON (formerly Claude S40)
Upstream repository: https://github.com/emir/AIKON
Pinned commit: 224516b3e6e7e1d2666abf95965102d9b5de1444
Pinned commit date: 2026-10-03

## Rule

This project reproduces the upstream implementation before modifying its architecture.

The reference is built by GitHub Actions from the upstream repository at the pinned commit. The source is not copied into this repository; provenance remains explicit.

## Verification order

1. Build and test the upstream Go server.
2. Build and package the upstream Java ME application.
3. Build the upstream Docker image.
4. Run the upstream top-level build.
5. Record CI results.
6. Only then evaluate extensions.

## Modification rule

Any future change to the reference-derived implementation must document what changed, why, evidence, tests, and compatibility impact.

## Cost rule

Mock/test mode and free CI are used first. Live provider calls or paid infrastructure are only used when they answer a specific verification question and are bounded.
