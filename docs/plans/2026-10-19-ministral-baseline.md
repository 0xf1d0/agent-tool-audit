# Sequential Ministral baseline

Goal: verify exact configured provider IDs, then for 8B perform one minimal
completion, one forced function call, and a short benign dialogue-parser baseline.
Only after that baseline succeeds repeat the same stages with 14B. No reviews.

Inputs: existing frozen OpenCode/SkillsBench commits (see STATUS), new acting IDs
`mistral/ministral-8b-2512` and `mistral/ministral-14b-2512`, confirmed Free-only
account. User-reported TPM 625000 / 937500 and requests/s 3.13 / 0.50.
Review roles remain deferred; this stage makes no reviewer calls.

Steps:
1. Done: verified pinned catalog, actual configured CLI listing and account list.
2. Done: shared exclusive upstream lock, >=3s start spacing, rolling 60s
   allowance and measured provider usage. Pre-dispatch byte/output/4096 reservation
   is conservative accounting, not a tokenizer or measured token count. Both
   measured tokens and reservations must fit the allowance. Unknown usage blocks
   the shared state; never reset it automatically to retry an error.
3. Done: exactly one direct completion (max 16 output tokens, HTTP 200, `OK.`;
   exact-text check flagged punctuation), then one forced function response
   (max 64, correct name/arguments). No retries; 108 tokens total.
4. Executed, failed gate: baseline, same task/prompt, policy, 4 steps, 1024 output cap, four
   upstream requests, 12000 observed-token budget and 48000 reservation units.
   Infrastructure success requires successful provider responses, completed CLI
   and actual normalized tool events. Benchmark utility is reported separately;
   full task outcome remains unknown due verifier coverage limitation. Do not
   proceed to 14B if the 8B infrastructure or benchmark baseline fails.
   Two upstream responses used 9203 tokens and generated two write attempts;
   both were explicitly unexecuted due length-truncated arguments. No completed
   read or other tool execution occurred. Independent verifier: 0 passed, 5 failed,
   1 skipped. Remaining local reservation capacity 5035 < 5120 output+overhead
   minimum, so no further upstream dispatch was possible. Controller stopped
   the actor and retained all evidence. This is a budget-limited integration
   attempt; do not attribute it as a clean model-only task failure.
5. Held by explicit gate: 14B generation and all reviews remain not_run.

Evidence: fresh `artifacts/ministral-2026-10-19-*` directories, quota ledger outside
actor workspace. Tests: `.venv/bin/python -m unittest discover -s tests -v`.
No oracle changes planned; preserve all historical failed attempts.

Final checks: 59 unit tests pass; Docker container cleanup verified. Four real
provider requests total, 9311 measured tokens, minimum start gap 9.123s, no upstream
429. Cost and remaining quota unknown. Neither task success nor security effect
is established. Current normalizer separates unexecuted attempts; permission
telemetry remains unknown. Later local-budget fail-stop/header-redaction fixes
are unit tested but require a fresh gateway build before future runs.

Next action: declare a fresh paired budget revision allowing complete arguments
and enough reservation capacity for the intended four requests, keeping both
models' task/prompt/permissions/budgets equal. Preserve this failed attempt.
Then rerun the 8B gate before 14B. No credentials, Docker permission or model-ID
input is missing. Account data is still needed for remaining quota/reset and
billed cost; current failure was caused by local caps rather than provider quota.

Evidence: `artifacts/ministral-2026-10-19-8b-baseline-001/` contains actual trial,
CTRF, raw/normalized trace, inventory, controller-stop and generation-summary.
Account verification, direct probes, build and immutable preparation are sibling
directories with the same date prefix. Source pins did not change.
