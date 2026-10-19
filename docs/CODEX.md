# Codex collaboration throughout the project

## Installation and project discovery
Open this repository root in VS Code with Codex. Initialize Git after extracting the ZIP. Codex discovers `AGENTS.md` along the directory hierarchy and project skills under `.agents/skills/`. If skills do not appear, restart Codex and verify your extension/CLI version. Project `.codex/rules/` requires a trusted project configuration layer; it does not override managed policy or provide OS isolation.

We use instruction roles, not an automatically spawned multi-agent runtime:
- **Experiment planner:** protocol, task selection, controls, budgets and version pins.
- **Tool auditor:** source-to-sink reasoning, CodeQL coverage, candidate/CWE evidence.
- **Runtime validator:** isolated reproducer, trusted oracles, permission telemetry, paired controls.
- **Evidence reviewer:** denominators, unknowns, source provenance, publication claims.

One Codex session can apply these roles sequentially. If you request parallel agents, assign different files and require evidence-based handoffs. Do not make a reviewer validate an expected answer supplied by the implementer.

## Starting prompts

**Plan:** “Use $plan-audit-pilot. Read the current status and build a reproducible three-task pilot from the pinned benchmark. Keep the directors' approximately twenty-task target visible. Identify exact missing inputs and implement everything that is unblocked.”

**Audit:** “Use $audit-tool-candidates. Inspect the selected OpenCode commit and real exposure inventory. Prioritize the observed high-authority tools, run available static analysis, and create evidence-backed candidate records. Do not infer a bypass from broad intended permissions.”

**Validate:** “Use $validate-audit-experiment. Implement the host-side oracle for this adjudicated candidate and test direct-tool vulnerable/patched controls before an agent run. Record permission coverage and unknowns.”

**Report:** “Use $report-audit-evidence. Produce a weekly update from actual artifact files. Separate synthetic engineering checks, candidate alerts, reviewer judgments and runtime-confirmed results. State the ASR denominator and missing telemetry.”

**WP3 extension:** “Design a transformation experiment on validated vulnerable/fixed pairs. Preserve behavior and trigger conditions, hold out related repositories/CVEs, and test detection/localization/CWE classification separately. Do not call model rationales causal explanations.”

## Session handoff
Update `docs/STATUS.md`: current stage, completed checks, evidence paths, unresolved decisions, blockers and next command. Use `PLANS.md` for larger work. Never place private code or raw prompts in the public status file. Use local ignored notes for confidential material.

## Verification
Run the unit suite for Python changes and the demo for oracle changes. Validate skill frontmatter (name/description) and paths after skill edits. Use `codex execpolicy check --rules .codex/rules/research.rules -- git push origin main` if supported by your CLI. Rule loading was not exercised in the delivered environment; review its output before relying on rules.

No API account, model IDs, system-wide skill installation or GitHub remote is configured by this archive.
