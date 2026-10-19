# From the demo to a real pilot

Run commands from the repository root. Outputs below use a fresh numbered directory; increment it when repeating. No command installs third-party tools automatically.

For the current pinned OpenCode v2 / Mistral Free-mode preparation, use
`docs/MISTRAL_BASELINE.md`. It records real source/model pins, task selection,
isolated image/gateway recipes, scarce-token limits and current host blockers.
The older generic commands below remain available; v2 uses `--standalone` and
different provider/permission configuration. The runtime adapter also accepts
immutable local `sha256:<64 hex>` image IDs from recorded builds.

## 1. Demonstrate the measurement workflow

```bash
python -m auditlab demo --out artifacts/demo-001
python -m auditlab inventory --trace artifacts/demo-001/trace.jsonl --risk configs/risk.json --out artifacts/demo-001/inventory.json
python -m auditlab report --input artifacts/demo-001/summary.json --out artifacts/demo-001/report.html
```

Four direct-tool cases should be produced. Only the vulnerable/adversarial case discloses the synthetic canary. All four complete the sum task. This is a test of the runner/oracle/report separation, not an agent study.

## 2. Pin real task and framework sources

Use clean, local Git checkouts of the agreed OpenCode and SkillsBench repositories under `vendor/`. Resolve repository redirects and commit hashes; do not assume the audit note describes the current release. Record each URL and commit in `configs/sources.template.json` after copying it to an experiment-specific file.

Inspect the pinned benchmark's task files and verifiers. Fill a copy of `templates/task-catalog.csv`, one task per row. The instruction path must be relative to the benchmark checkout and point to a file. This deliberate curation supports both old and new upstream task formats. Order candidates according to the declared selection rule.

```bash
python -m auditlab select-tasks --catalog artifacts/task-catalog.csv --root vendor/skillsbench --count 20 --out artifacts/selection.json
```

If fewer than 20 eligible tasks exist, the command stops with the actual count. Revise the scope explicitly or select three for the pilot. Never create fabricated benchmark IDs. Check source license and task environments; the tool does not download or adapt the benchmark automatically.

## 3. Freeze model, tool and policy choices

Copy `configs/pilot.template.json` to `artifacts/pilot.json`, resolve all REQUIRED fields and populate real task IDs. Use two distinct exact provider/model identifiers. Pin the framework commit, immutable runtime image, policy hash and source revisions in the run's evidence bundle. `plan` creates a schedule only; it does not assert that these experiments ran.

```bash
python -m auditlab plan --config artifacts/pilot.json --out artifacts/matrix.json
```

Three tasks × two models × two versions × two input conditions × three repetitions = 72 planned runs. Start with benign baseline exposure before building all attack conditions.

## 4. Capture an OpenCode baseline

Prepare a disposable copy of one task, outside this repository's evidence directories. Build or obtain an image containing the pinned OpenCode version, the task's dependencies and provider configuration. Use its immutable registry digest. The image must run as UID 1000, support a read-only root and writable /tmp, and have `opencode` on PATH. Make the disposable task directory writable to UID 1000; do not change permissions on original datasets.

The repository deliberately does not ship a moving-tag Dockerfile or assume a provider account. First build a command without executing it:

```bash
python -m auditlab run-opencode --image 'YOUR_IMAGE@sha256:YOUR_64_HEX_DIGEST' --workspace /absolute/disposable-task --model provider/exact-model --prompt /absolute/task-instruction.txt --out artifacts/baseline-001
```

The example digest is a placeholder and must be replaced. The default network is `none`; live models require a dedicated lab network with a model gateway configured in the image. Add `--network YOUR_LAB_NETWORK` and, when necessary, `--env PROVIDER_API_KEY`, then `--execute`. Environment variable values are read by Docker, not placed on the command line. A provider credential passed into the container is visible to its tools: prefer a scoped gateway token with a short lifetime and restricted access. Never pass a personal unrestricted key into an adversarial run.

The adapter caps CPU, RAM, PIDs and elapsed time. Network names are not egress policies: configure the lab network/gateway externally. For adversarial tasks prefer disposable VMs in addition to containers. Never use host networking or a Docker socket mount. OpenCode may require release-specific writable cache settings; adjust the image and document them, not the evidence boundary.

`execution.json`, `raw.jsonl` and `stderr.log` stay on the controller. On timeouts the named container is removed. No runtime security verdict is inferred from CLI output or exit status. Verify `opencode run --help` inside the pinned image: the command is based on current CLI documentation and has not been tested against your chosen build.

## 5. Normalize traces and rank tools

```bash
python -m auditlab normalize-trace --input artifacts/baseline-001/raw.jsonl --out artifacts/baseline-001/trace.jsonl
python -m auditlab inventory --trace artifacts/baseline-001/trace.jsonl --risk configs/risk.json --out artifacts/baseline-001/inventory.json
```

Inspect the adjacent `.coverage.json`. Zero normalized calls is not proof no tools ran. The supported event shape is `type=tool_use`, `part.tool`, `part.callID`, `part.state.status/input`; unknown shapes must be inspected and the adapter extended with a real redacted fixture. Inputs can contain sensitive material; keep traces private. Risk dimensions (0–3) are analyst judgments; initial OpenCode entries in `risk.json` are hypotheses, not validated findings. Unknown tools get no score, not a zero-risk score.

## 6. Run CodeQL and triage

```bash
python -m auditlab codeql-plan --source vendor/opencode --language javascript-typescript --out artifacts/codeql-001
```

Inspect `plan.json`. To execute, run again with a NEW output directory and `--execute`, inside a disposable analysis environment with CodeQL installed. Pin query packs and CLI version in that environment. Compiled C/C++ targets may need a custom build/extraction command; inspect the generated plan and record changes rather than assuming automatic extraction worked. CodeQL queries do not cover every permission logic flaw.

```bash
python -m auditlab sarif --input artifacts/codeql-002/findings.sarif --out artifacts/candidates.jsonl
python -m auditlab review-packets --findings artifacts/candidates.jsonl --out artifacts/review-packets-001
```

For a format-only demonstration use `examples/synthetic.sarif.json` instead of a real scan. It is hand-authored and labelled synthetic; its alert does not prove CodeQL detects the demo.

## 7. Independent LLM review

Attach pinned source context, callers and policy to each packet. Submit independently to reviewer A and reviewer B through your selected provider interfaces. Record model/version, prompt, raw response and usage. Save each response object as one line in `review-a.jsonl` and `review-b.jsonl`. Follow the response template; do not use fabricated answers.

```bash
python -m auditlab compare-reviews --a artifacts/review-a.jsonl --b artifacts/review-b.jsonl --out artifacts/review-comparison.json
```

Agreement is not confirmation. Complete `templates/finding.md` and have evidence adjudicated. Keep reviewer decisions separate from acting-agent behavior.

## 8. Validate a selected candidate

Implement the candidate-specific tool harness and host oracle using `templates/oracle.md`. Start with direct invocation and vulnerable/patched controls. Then use the same scenario in a legitimate agent task. Record correlated permission events for boundary claims. This case-specific instrumentation is research work, not generated automatically by the generic OpenCode adapter.

Store one outcome per run following `examples/run-record.json`. Unknown values remain null. Validate and summarize:

```bash
python -m auditlab summary --input artifacts/real-runs.jsonl --out artifacts/real-summary.json
python -m auditlab report --input artifacts/real-summary.json --out artifacts/real-report.html
```

Do not fabricate oracle fields from model statements. Keep raw trial records and failed attempts, and add expected but unexecuted runs as not_run with null outcomes when reporting coverage.

## 9. Optional Luxembourg intake

```bash
python -m auditlab import-pairs --input data/private/method_level.json --out artifacts/method-pairs.jsonl
```

Importer output preserves unverified source labels and repository grouping. It does not build programs, infer CVE correctness, or join repository/file-level metadata. Keep raw private code out of the public repository.
