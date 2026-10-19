# Agent Tool Audit

**A reproducible workflow for studying software vulnerabilities in the tools of coding agents.**

Week-two research pilot: OpenCode → software-engineering tasks → two acting LLMs → observed tool usage → risk prioritization → CodeQL → CWE candidates → independent LLM review → controlled runtime validation.

**Status: working local demonstration and research tooling; no OpenCode vulnerability has been confirmed by this repository.** The included demonstration uses one intentionally vulnerable Python fixture and its repair. It calls no LLM and does not execute OpenCode or CodeQL. Real experiments require the pinned dependencies and model access described below.

## Start in five minutes

Requirements: Python 3.11+; Git for provenance and task selection. No Python dependencies are needed for the local demo.

```bash
python -m auditlab doctor
python -m unittest discover -s tests -v
python -m auditlab demo --out artifacts/demo-001
python -m auditlab report --input artifacts/demo-001/summary.json --out artifacts/demo-001/report.html
```

Open `artifacts/demo-001/report.html` in a browser. In VS Code, open this directory, then **Terminal → Run Task → AuditLab: demo**. Use a new output directory on subsequent runs; experiments are not silently overwritten. `docs/demo-report.html` is a pre-generated example from the shipped fixture, not a research result.

Windows: use `py -3` in place of `python` if needed. Docker experiments are easiest in a Linux environment or WSL2. An optional editable install is `python -m pip install -e .`; the direct `python -m auditlab` commands do not require it.

## What is implemented

| Stage | Implementation | Evidence status |
|---|---|---|
| Task selection | Validate curated CSV, filter easy/medium SWE tasks, pin clean checkout and instruction hashes | Ready; real task manifest not yet populated |
| Agent execution | Docker command builder, dry run, timeout and output capture for OpenCode CLI | Unit-tested; live Docker/OpenCode run pending |
| Tool inventory | Normalize terminal OpenCode tool events, retain coverage counts, rank with explicit risk dimensions | Tested on documented fixture shape; verify against chosen OpenCode release |
| Static analysis | CodeQL command planning/execution; SARIF 2.1.0 import with CWE tags and code flows | SARIF tested; live CodeQL scan pending |
| Two-model review | Evidence packets, structured review responses, disagreement comparison | Offline/manual model submission; no API billing |
| Runtime validation | Executed vulnerable/patched × benign/adversarial local fixture and controller oracle | Synthetic demonstration only; real task-specific host oracles must be added |
| Dataset intake | Import method-level Luxembourg JSON schema; preserve labels as unverified | Schema fixture tested; full dataset not bundled |
| Reporting | Validate run records, preserve unknowns, grouped run-level ASR/utility, HTML report | Tested; no invented costs or model scores |

## Research question

Under which task, input and permission conditions does a candidate defect in a coding-agent tool become reachable and cause a verified unauthorized effect?

This is the directors' initial applied pipeline. The broader PhD studies mechanistic interpretability (WP2) and problem-space attacks against LLM vulnerability detection (WP3). This repository connects to those packages through evidence-based LLM review and a later robustness track; it does not assume the directors replaced the formal thesis objectives.

## Run the real workflow

Follow [the runbook](docs/RUNBOOK.md). Start with three validated task environments, then expand toward the requested approximately twenty tasks after checking the actual benchmark revision and task availability. Do not invent task IDs to meet a count.

- **Choose two exact acting models yourself** in `configs/pilot.template.json`; do not confuse the coding agent with an LLM reviewer.
- Select the actual OpenCode repository and commit. The supervisor audit note mentions `sst/opencode`; treat locations and candidate defects as version-specific hypotheses.
- Put source checkouts in ignored `vendor/`, confidential datasets in ignored `data/private/`, and raw outputs in ignored `artifacts/`.
- Keep model provider credentials out of files, logs and Git. Real runs must use disposable workspaces, never this research repository as their task workspace.

## Working with Codex

Open the repository in VS Code with Codex, or start Codex from its root. `AGENTS.md` contains the project contract; `.agents/skills/` contains four reusable workflows. Project command rules are in `.codex/rules/research.rules`; they depend on Codex project trust and are not a security sandbox.

Start with:

> Read AGENTS.md, docs/STATUS.md and docs/RUNBOOK.md. Use $plan-audit-pilot to identify the next unblocked step. Preserve the distinction between candidates, synthetic demonstrations and confirmed runtime findings. Do the work, run relevant checks, and update STATUS.md with evidence and the next step.

See [Codex workflow](docs/CODEX.md) for focused prompts, review roles, and handoff conventions.

## Repository map

| Path | Purpose |
|---|---|
| `auditlab/` | Dependency-free Python workflow CLI |
| `tests/` | Regression tests for evidence, denominators and adapters |
| `configs/` | Explicit model/task/policy and risk templates |
| `examples/` | Clearly marked synthetic input formats |
| `templates/` | Finding, task and oracle specifications |
| `docs/` | Protocol, runbook, status, next-week demo, sources |
| `.agents/skills/` | Planning, auditing, validation and reporting skills |
| `.codex/rules/` | Small command-review rules; not runtime confinement |
| `.github/` | CI and research issue/PR templates |

## Publish on GitHub

The ZIP excludes `.git` and contains no uploaded thesis PDFs or original datasets. After extraction:

```bash
git init -b main
git add .
git commit -m "Initialize agent-tool audit research workflow"
```

Create an empty GitHub repository, then use its displayed remote URL:

```bash
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```

Inspect `git diff --cached` before the initial commit. Raw runs are ignored; publish only reviewed, redacted evidence. No code license is assigned yet: choose one with your institution before advertising reuse rights. See [publication guidance](docs/PUBLICATION.md).
