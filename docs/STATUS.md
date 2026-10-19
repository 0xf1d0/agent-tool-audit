# Research status

## Current milestone

### Paired budget retry (latest, 2026-10-19)

The user-approved revision is deployed in fresh images: output 4096 in provider
body, both acting model limits and gateway; four upstream requests/four steps;
524288 cumulative reservation units; 32768 observed-token stop threshold.
The observed limit is **not a hard cap**: a final admitted request may overshoot,
and subsequent dispatch stops. Reservation units remain byte/output/overhead
accounting, separate from measured provider tokens. Final serialized payloads
are now capped at 98304 bytes; four maximum requests reserve at most
4*(98304+4096+4096)=425984 units, leaving 98304 units of headroom.
Tests exercise serialization growth, maximum-size requests and threshold overshoot.

One fresh benign `mistral/ministral-8b-2512` retry completed with exit 0 and four
HTTP 200 responses. It used 15055 prompt + 2171 completion = **17226 tokens**,
and 108604 reservation units. Output counts per request: 866, 34, 831, 440;
no output cap was reached. Starts were separated by at least 3.000189s; gateway
timestamps show no overlap. No provider 429, threshold crossing or local-budget
rejection occurred. Cost and remaining account quota remain unknown.

Three terminal tool events: `/app/solution.py` write returned permission error
`external_directory`; `shell` (`ls -la /work`) and `/work/solution.py` write
completed. Only solution.py was retained; dialogue.json and dialogue.dot were
absent. Step four disabled tools and requested a text-only wrap-up, consistent
with the pinned four-step implementation. This ceiling, including the initial
path-denial detour, constrained completion; model incapability is not established.
CLI finish reasons are `tool-calls` for the first three requests. The final text
response has no captured step_finish event, so its exact finish reason is unknown.
No length truncation was observed; all measured outputs are below 4096.

Independent pytest: **31 setup errors, 4 skips, 0 passes**, caused by missing
output data. CTRF contains six function-level entries (5 failed, 1 skipped),
not the same denominator as the parametrized pytest cases. Benchmark outcome
is false; full task outcome stays unknown under the existing parse_script oracle
coverage limitation. The agreed 8B gate has **not passed**. 14B and all 78 reviews
remain on hold. Permissions/policies, task prompt, source pins and Free-only mode
were preserved; no permission control was relaxed to work around the path denial.

62 tests passed before the retry; 63 pass after a post-run normalizer correction:
`providerResult.executed=false` means not provider-hosted, not that a local tool
failed to execute. Completed local tools now count correctly. Explicit framework
length-truncation errors still establish unexecuted arguments; permission errors
and full permission telemetry remain unknown. Original normalized outputs are
retained; use **trace-v2.jsonl, inventory-v2.json and provenance-v2.json** for this
retry. This changes controller analysis only, not the evaluated runtime or budgets.

Evidence: `artifacts/ministral-2026-10-19-prep-002/`,
`artifacts/ministral-2026-10-19-build-002/embedded-config-checks.json` (image
configurations equal prepared files), and
`artifacts/ministral-2026-10-19-8b-baseline-002/` (raw/normalized traces,
generation-summary, baseline-assessment, immutable image IDs, verifier output,
run-records-v2/summary-v2/report-v2). Disposable container cleanup was verified.
Failed baseline-001 is preserved. Plan:
`docs/plans/2026-10-19-paired-budget-revision.md`.

### First Ministral attempt (historical, 2026-10-19)

2026-10-19 update (supersedes the earlier model-access blocker below): selected
acting models are now `mistral/ministral-8b-2512` and
`mistral/ministral-14b-2512`, per user instruction. Both exact IDs were verified
in the pinned catalog, actual configured OpenCode CLI listing and authenticated
Mistral model list. 8B direct completion returned HTTP 200 (`OK.`, 11 tokens;
the exact-text checker flagged punctuation); its forced function-call probe
passed with 97 tokens. The fresh 8B baseline failed: two generated write calls
were truncated at the 1024-output-token cap and explicitly never executed.
Its two upstream requests succeeded (9203 tokens), then local cumulative
reservation budget exhaustion prevented further dispatch. The controller stopped
the actor and the independent verifier recorded 0 passed / 5 failed / 1 skipped.
This is a budget-limited integration attempt, not a provider-quota failure or a
clean model-task-failure measurement. Full task outcome remains unknown under
the existing oracle coverage limitation; benchmark outcome is false.
No 14B generation or review call was made, honoring the successful-8B-baseline gate. See
`docs/plans/2026-10-19-ministral-baseline.md` and fresh
`artifacts/ministral-2026-10-19-*` evidence. Historical failures remain below.

Current checks: 59 unit tests pass. Four successful provider requests consumed
7248 prompt + 2063 completion = 9311 measured tokens, with minimum start spacing
9.123 seconds and no upstream 429. Cost and remaining quota remain unknown.
Gateway controls now share a process-exclusive pacing state across probes and
containers and reserve rolling 60s capacity using byte/output/overhead units,
then replace reservations with measured provider usage. These units are not an
exact tokenizer. Local budget exhaustion stops subsequent retries. The latter
fix is unit-tested after the attempt and is not in the already-built image.
The first normalizer interpreted `providerResult.executed=false` as unexecuted;
the latest update corrects that interpretation. The explicit length-truncation
errors still establish that this run contains zero completed
tool executions, two explicitly unexecuted write attempts, permission unknown.

Next concrete step: prepare a new paired budget revision before another live
attempt. Current 48000 cumulative reservation units leave only 5035 after two
requests, below the 5120 output-plus-overhead minimum for another default call;
1024 output tokens also truncate the generated tool arguments. Increase output
and reservation allowances consistently for both actors while retaining explicit
request/observed-token caps, then rerun the 8B gate before any 14B generation.
No additional credential, Docker permission or exact model identifier is needed.
Account remaining quota/reset and billed cost still need provider account data;
they did not block the four successful requests. All 78 reviews remain unlaunched.

New evidence: `artifacts/ministral-2026-10-19-account-002/preflight.json`,
`ministral-2026-10-19-prep-001/`, `ministral-2026-10-19-build-001/`,
`ministral-2026-10-19-8b-completion-001/`, `ministral-2026-10-19-8b-function-001/`,
and `ministral-2026-10-19-8b-baseline-001/` under `artifacts/`. The last directory
contains trial/CTRF, raw and normalized traces, execution-aware inventory,
controller-stop explanation and generation-summary. Shared quota state is in
`artifacts/ministral-2026-10-19-pacing/`, never mounted into the actor.

Earlier checkpoint (2026-10-15): Docker access and Mistral Free-mode confirmation were resolved. Pinned images
built and both primary benign attempts ran, but each Mistral completion request
returned HTTP 429. No model completion/tool exposure was observed. Isolated
CodeQL extraction and analysis completed, yielding 78 provisional repository-wide
alerts; no product vulnerability has been confirmed.
The directors' OpenCode → SWE tasks → two actors → exposure → CodeQL/manual
candidates → two-model review → direct-tool → agent validation pipeline remains
the objective. WP2/WP3 remain later extensions.

## Completed preparation on 2026-10-14 (historical)

- Clean shallow source checkouts: OpenCode
  `943dc005f792d401b0dd24dd965082bdcb3a5f09` (2.0.29, MIT) and SkillsBench
  `f860ecf02ef53412a030f8661c83d644b739ff01` (Apache-2.0). “Latest” was resolved
  at fetch time and frozen; no moving source reference is used for trials.
- Inspected real task metadata, environments and verifiers. CLI selection of
  20 reports nine eligible easy/medium primary SWE tasks by static curation.
  Runtime reproducibility remains unverified. Declared ordering selects
  `dialogue-parser`, `fix-build-agentops`, `fix-build-google-auto` for the pilot.
- Selected Mistral Small 4 (`mistral/mistral-small-2603`) and Medium 3.5
  (`mistral/mistral-medium-3-5`). Authenticated read-only model listing confirms
  both IDs and chat/function-calling capabilities. Generation access, remaining
  account quota and billing are unknown. Same products will review independently
  in separate sessions, after real candidates exist.
- Prepared the first dialogue task input and instruction body separately from
  verifier/reference files; source, prompt, policy and build-context hashes.
  One task × two actors × one repetition is the declared scarce-token smoke
  stage. Three-task and approximately 20-task stages remain later targets.
- Implemented a fixed-upstream scoped gateway, per-trial model/token/request/
  byte/output/time limits and independent usage ledger. Prepared source-built
  actor, separate verifier and gateway Docker targets with digest-pinned Bun and
  Python bases. Added OpenCode v2 configuration and private-server support.
- Implemented a controller driver with fresh workspace/networks, pre-run network
  probes, gateway-only credential delivery, separate verifier and cleanup records.
  These integrations have only local unit/dry-run coverage; no image has built.
- Located CodeQL 2.27.2 at `/opt/codeql/codeql`; recorded a dry-run source scan
  plan pinned to installed JavaScript queries 2.4.7. No extraction/scan executed.
- At that checkpoint, all 45 unit tests passed under `.venv/bin/python` 3.14.4. Compile check and
  fresh synthetic demo/inventory/report passed. Gateway and baseline dry runs
  passed their planning checks; unresolved controlled matrix correctly rejected.

## Historical blockers and checks recorded on 2026-10-15

1. **Mistral generation:** Small 4 and Medium 3.5 each received HTTP 429 on one
   upstream request. Medium's provider error is rate_limited / 1300 / Rate limit
   exceeded, without Retry-After. Stop further calls until the provider limit
   clears; remaining quota/reset time and billed usage are unknown. The .env key
   and true Free-only flag were verified without printing the key.
2. **Static triage/review:** CodeQL completed in codeql-live-003, reusing the
   finalized database and saved source-compilation cache after prior extraction/
   timeout failures. It produced 78 alerts, all candidate. Repository-wide scope
   precedes exposure because Mistral is blocked; relevance to actual tools and
   independent reviews still need validation. Both reviewer models use Mistral.
3. **Runtime validation:** actor/verifier/gateway images built; CLI/config loading,
   readonly-root cache setup and pre-run network probes passed. Successful provider
   streaming, actual tool invocation and effective runtime permission behavior
   remain unverified. The two selected BugSwarm tasks still need dedicated
   image/path/reference-separation adapters; dialogue's runtime is prepared.
4. **Trace/oracle coverage:** v2 emits `part.id`, which the current normalizer already accepts along
   with callID. Earlier documentation saying otherwise was inaccurate. All four
   raw captures normalize to zero calls; no real tool-event fixture is available.
   Permission telemetry stays unknown. The dialogue verifier omits the requested
   `parse_script` function check, so `benchmark_task_success` is separate and
   full `task_success` stays null until supplementary functional checks exist.
5. **Later stages:** finish isolated CodeQL analysis, observed-tool source triage,
   independent real reviews, candidate-specific repair/attacker surface/host
   oracle, direct controls and agent validation are still outstanding.

## Evidence paths

Current local ignored bundle: `artifacts/mistral-baseline-prep-001/`:

- `sources.json`, `task-catalog.csv`, `task-inspection.json`, `selection-shortage.json`,
  `selection-3.json` and actual CLI selection logs/output;
- `baseline.json`, `pilot.unresolved.json`, `prompt.txt`, `initial-input/`,
  `build-context/`, digest manifests in `base-resolution-002/`;
- `image-build/build.json` and failed actor build log (other targets not_run);
- `account-preflight-003/preflight.json` (successful model list, no generation);
- `codeql-version.json`, `codeql-plan-001/plan.json` (not executed);
- `checks.json`, check logs, gateway/baseline dry runs, fresh `synthetic-demo/`
  and `manifest.sha256.json`.

Prior preparation remains in `artifacts/first-real-prep-001/`. Artifacts, vendor
sources and `.env` remain ignored; no datasets, secrets or traces are published.
The controller repository has no `.git` checkout; its file hashes substitute for
a controller commit until version control is established.

## Checks completed on 2026-10-15

All 55 unit tests pass on .venv Python 3.14.4. Compile checks and a fresh synthetic
demo pass. Regression coverage includes prompt_cache_key, redacted HTTP quota
errors, rootless workspace helper boundaries, readonly/no-network CodeQL planning,
source-revision drift, finalized-database/cache reuse provenance and a real SARIF
column-collision regression. Different-column alerts on the same line now retain
separate IDs, and duplicate IDs cannot silently overwrite review packets. These checks
are local engineering evidence; no model generation or exploitation is inferred.
Check logs and synthetic outputs are in `artifacts/live-evidence-2026-10-15-001/`.

## Live evidence on 2026-10-15

- `artifacts/live-baseline-2026-10-15-001` through `-005`: preserved build/context
  revisions, immutable image IDs and runtime checks. Fixed binary copy path,
  tmpfs HOME/cache initialization and rootless disposable-workspace ownership.
  Controller-only persistent mounts retain gateway and verifier evidence.
- `artifacts/live-small4-001` and `-002`: two integration attempts with gateway
  schema errors; first gateway/CTRF tmpfs evidence was lost and stays unknown.
  Bounded prompt_cache_key support now has regression coverage.
- `artifacts/live-small4-003` and `artifacts/live-medium35-001`: one upstream
  request per actor, HTTP 429, no successful generation or parsed tool event.
  Independent benchmark checks failed on absent outputs. Full task/security/
  permission outcomes and measured tokens/cost stay unknown.
- `artifacts/live-evidence-2026-10-15-001/{run-records.jsonl,summary.json,report.html}`:
  validated records, two integration attempts separated from two primary model
  attempts, all benign ASR entries null. This is an integration checkpoint, not
  a model performance comparison or vulnerability result.
- `artifacts/codeql-live-001`: extraction failure (missing Node).
  `codeql-live-002`: finalized database and analysis timeout with saved query
  cache. `codeql-live-003`: completed analysis, same source/CLI/query pins and
  readonly network-free isolation. Coverage: 5087/5113 JavaScript/TypeScript files,
  32/32 Actions files extracted; JavaScript/TypeScript security query suite only.
  26 unscanned paths are recorded in coverage-summary.json. SARIF invocation
  executionSuccessful=true; no warning/error-level SARIF notifications.
  Repository-wide pre-exposure scanning is a recorded stage-order deviation.
- `artifacts/codeql-live-003/candidates-v2.jsonl`: 78 unique column-aware candidate
  IDs; original import retained (78 alerts/77 IDs exposed the fixed collision).
  `review-packets-context/`: 78 source-linked packets, no reviews executed.
  `findings/1f59b15d85910734.md`: portable Zsh scanner regex candidate with pinned
  caller chain, configuration preconditions, counterexamples and unverified effect.
  `triage-summary.json` records scope and counts; no observed-tool ranking.

## Next executable step

The fresh 8B budget retry completed infrastructure and real local tool execution,
but hit the four-step ceiling before generating JSON/DOT. The next experiment
needs a declared paired step/request-budget revision; choose the next identical
allowance for both actors, recalculate cumulative reservation headroom against
final payload size, and rebuild a fresh context before one further 8B attempt.
Keep the selected Ministral IDs and current task/permissions, output 4096 and
observed stop threshold 32768 fixed unless explicitly revising them. The `/app`
write denial is an actual policy constraint; do not silently relax it. Capture
the final response finish reason in future telemetry, which is missing here.
Do not retry Small 4 or treat the superseded HTTP 429 as the current blocker.
No additional key or Docker access is needed. No paid fallback is authorized.

Keep 14B generation and all reviews on hold until 8B completes the agreed gate;
neither model incapability nor vulnerability exploitation follows from this run.
Execution plan: `docs/plans/2026-10-19-paired-budget-revision.md`.
Original pins and historical preparation remain preserved. No candidate is
review_supported, direct_tool_validated or agent_validated. WP2/WP3 remain later
extensions. Synthetic fixtures and mocks remain engineering evidence only.
