---
name: validate-audit-experiment
description: Implement or validate direct-tool and agent-in-the-loop experiments, runtime adapters, permission telemetry and security-effect oracles. Use for runs and evidence correctness.
---

# Validate an audit experiment

1. Read `docs/PROTOCOL.md`, `templates/oracle.md` and the candidate's source evidence. Define true, false and unknown before executing.
2. Keep host/controller oracles, reference fixes, outcome files and private data outside the agent workspace. Use a fresh disposable task copy for every run.
3. Establish direct-tool vulnerable/patched × benign/adversarial controls. Do not infer semantic preservation from compilation alone.
4. For real OpenCode, inspect the `run-opencode` dry run, pinned image and restricted gateway setup in the runbook. Raw agent logs do not prove a security effect. Ordinary CLI events leave permission state unknown.
5. Correlate independent canary/boundary evidence with complete permission instrumentation before calling a silent gate bypass. Add a versioned real event fixture when extending the normalizer.
6. Validate run records with `summary`; preserve failed attempts, timeouts and missing telemetry. Run unit tests and the synthetic demo after oracle changes. Clearly state which external integrations were not exercised.
