# Research status

## Current milestone

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
The normalizer/inventory now preserve `providerResult.executed=false`, separating
terminal tool attempts from actual executions. This run contains zero completed
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

Resolve Mistral HTTP 429 using actual remaining quota and request/token limits
(the API provided no reset time). Then resume Small 4 from the built images in
live-baseline-2026-10-15-005, using a fresh output directory; capture real tool
exposure before prioritizing candidates. Review the prepared static packets in
independent sessions once quota permits. Direct/agent validation requires a
candidate-specific oracle and paired controls. No paid fallback is authorized.

Execution plan: `docs/plans/2026-10-15-live-baseline.md`. Original pins and
historical preparation remain above and in the prior plan. No candidate is
review_supported, direct_tool_validated or agent_validated. WP2/WP3 remain later
extensions. Synthetic fixtures and mocks remain engineering evidence only.
