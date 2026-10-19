# A ten-minute director demonstration

1. **Research question (1 min):** show README and the distinction between tool defects, agent reachability and operational effects. Present this as implementation of the directors' week-two pipeline.
2. **Reproducible workflow (2 min):** show the protocol, selected-source templates, separate acting/review model roles and candidate status gates.
3. **Live local demonstration (2 min):** run `python -m auditlab demo --out artifacts/meeting-demo-001`, generate its report, open it. Explain clearly: one synthetic direct-tool scenario; zero LLM/OpenCode/CodeQL calls. Show both legitimate utility and the canary effect.
4. **Evidence handling (2 min):** ingest the synthetic SARIF fixture, create review packets, show how unverified CWE labels and unknown verdicts remain explicit. Do not present fixture findings as scanner output.
5. **Real pilot readiness (2 min):** show the OpenCode dry-run command, risk inventory format, and task manifest. If real data exists by the meeting, show its provenance; otherwise state the missing environment/model choices.
6. **Next experiment (1 min):** agree the first eligible tasks and exact model IDs, then select one audit-note candidate after source verification.

Success criterion: directors can see executable infrastructure and a concrete next experiment. A fabricated large result table is never a substitute for this.
