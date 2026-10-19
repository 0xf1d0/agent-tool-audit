---
name: plan-audit-pilot
description: Plan the directors' coding-agent tool audit pipeline, select tasks and models, or resume a blocked research stage. Use for experiment design, not for claiming completed runs.
---

# Plan an audit pilot

1. Read `docs/STATUS.md`, `docs/PROTOCOL.md` and the relevant `docs/RUNBOOK.md` stages.
2. Preserve the directors' pipeline and distinguish acting models from reviewing models. Treat approximately twenty tasks as a selection target, not an assertion about available tasks.
3. Inspect pinned local sources and executable task verifiers. Use `python -m auditlab select-tasks` with a curated catalog. Report shortages rather than inventing IDs.
4. Resolve exact source, model, image and policy metadata in a copy of `configs/pilot.template.json`. Generate the schedule with `python -m auditlab plan`; label it unexecuted.
5. Define attacker control, protected boundary, direct-tool controls and independent oracles before running attacks. Keep WP2/WP3 as documented extensions.
6. Complete useful local preparation if credentials or tools are absent. Record missing inputs, next executable action and deviations in STATUS and an execution plan. Never repeatedly ask permission for reversible local work.
