---
name: report-audit-evidence
description: Write research updates, ASR and utility tables, meeting reports or publication claims from audit artifacts. Use when summarizing completed work; do not fill missing observations with examples.
---

# Report audit evidence

1. Read STATUS, PROTOCOL and actual source artifacts for every claim. Separate planned work, synthetic demonstrations, static candidates, reviewer judgments and runtime validation.
2. Use `python -m auditlab summary` and `report` on validated records. State run-level denominators, unknown counts and missing cost coverage. Keep benign side effects separate from adversarial ASR.
3. Do not combine fixture/model-free results with real agents. Do not treat repeated oracle checks as independent runs or compare these run-level rates directly with HarnessSecurity-Bench oracle-level ASR.
4. When reviewers agree on a CWE, report agreement unless independent ground truth establishes correctness. LLM explanations do not establish causal interpretability.
5. Report source/model/configuration pins, limitations and a concrete next step. Use `docs/NEXT_WEEK_DEMO.md` for a director walkthrough.
6. Redact private material before proposing publication. Update STATUS with artifact paths. Do not send email or push GitHub changes unless requested.
