# Delivery validation

Validated locally on 2026-10-14 with Python 3.12.14 and Git 2.51.1.

## Executed

- `python -m unittest discover -s tests -v`: **26 tests passed**.
- `python -m compileall -q auditlab`: passed.
- Local synthetic demo: four version/input controls; only vulnerable/adversarial disclosed the controller canary; all four completed the legitimate sum task.
- CLI inventory, report, SARIF ingestion, review-packet generation and trace normalization smoke tests: passed.
- Four Codex skills: initialized and frontmatter-validated with the skill-creator helper.
- Independent skill forward test: unit suite, fresh demo, inventory, HTML report and OpenCode dry run. Found failure-recording issues, subsequently repaired and covered by regression tests.
- Failure probes: mocked Docker cleanup timeout preserves execution outcome; mocked CodeQL timeout records a failed attempt; unexecuted runs cannot carry observed outcomes; invalid permission states are rejected.

The generated `docs/demo-report.html` is based on executed synthetic fixture outcomes. No model/API cost was incurred by the research workflow.

## Not executed here

Docker, OpenCode, CodeQL and the Codex CLI are not installed in the delivery environment. Therefore live container/provider execution, real CodeQL extraction, actual OpenCode event-schema compatibility, rule loading, permission instrumentation and real SkillsBench tasks remain unverified. GitHub Actions is configured but has not run on GitHub. Only Python 3.12 was exercised locally; CI specifies 3.11–3.13.

No real LLM review, confirmed OpenCode weakness, dataset-wide claim or model benchmark result is included. Test mocks verify control flow, not external-tool compatibility. A real pilot needs the source/model/image/policy choices and candidate-specific trusted oracle described in RUNBOOK.
