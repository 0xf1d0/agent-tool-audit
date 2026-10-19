# Paired budget revision, retry 1

Goal: rebuild and retry exactly one fresh benign 8B baseline with user-approved
engineering settings. Preserve failed baseline-001. Keep 14B and reviews held
until successful 8B infrastructure, executed tools and all benchmark checks.
Full task outcome remains unknown under the pre-existing verifier coverage gap.

Pins: unchanged OpenCode 943dc005f792d401b0dd24dd965082bdcb3a5f09,
SkillsBench f860ecf02ef53412a030f8661c83d644b739ff01. Actors remain
mistral/ministral-8b-2512 and mistral/ministral-14b-2512.
Same task, instruction, tool permissions and sampling; same revised caps for both.

Steps:
1. Done: provider body/both model limits/gateway output = 4096;
   max_requests/agent steps = 4; cumulative reservation units = 524288;
   observed-token stop threshold = 32768. Record final-request overshoot semantics.
2. Done: enforce final serialized payload <=98304 bytes; unit-test
   four-request reservation bound 4*(98304+4096+4096)=425984, leaving 98304 units.
   Reservation units are not measured tokens or exact tokenizer bounds.
3. Done: 62 tests passed before live run; regenerate fresh prep/build context, build
   images and independently inspect embedded limits before a dry run.
4. Done: one fresh 8B baseline sharing prior pacing state, one upstream call
   in flight, >=3s start gaps, rolling per-model quota control, no paid fallback.
5. Done: inspect finish reasons, executed/not-executed/unknown calls, provider
   tokens, verifier outcomes, truncation and four-step ceiling; update STATUS
   including its bottom Next executable step. No 14B or review call in this retry.

Validation: `.venv/bin/python -m unittest discover -s tests -v`. New evidence
under ministral-2026-10-19-prep-002/build-002/8b-baseline-002; never overwrite 001.
Budget settings are provisional engineering controls, not task-success evidence.
No oracle changes or security experiments. Remaining provider quota/cost unknown.

Decision: retain the existing pre-request measured-token stop threshold (soft),
as explicitly allowed by the user. A request admitted below 32768 may take usage
above it; further requests stop. Do not mislabel byte reservations as a hard token
cap. Tests cover both overshoot followed by stopping and final serialization growth.

Result: four HTTP 200 responses, process completed, 15055 prompt + 2171 completion
=17226 measured tokens. Reservation units 108604; largest final payload 23539
bytes. Minimum start gap 3.000189s and no inflight overlap. No 429 or local budget
failure. CLI finish reasons tool-calls x3; final response exact reason unknown
(no step_finish in raw). All measured outputs below 4096; no truncation detected.

Two completed local tools: shell listing /work and write /work/solution.py.
Earlier write /app/solution.py returned external_directory permission denial.
Four-step implementation forces text-only wrap-up on step four, leaving only
three tool-enabled steps here. JSON/DOT were not generated. Pytest reported
31 setup errors and 4 skips; CTRF reduced this to six function-level entries
(5 failed, 1 skipped). These denominators are distinct. Benchmark false, full task
outcome unknown under original coverage limitation. This is not model incapability.
14B and all reviews remain unexecuted because the 8B gate did not pass.

Post-run evidence correction: providerResult.executed=false identifies non-hosted
execution; local shell/write may complete with it. Corrected normalizer and real
schema regression pass all 63 tests. Retained original v1 normalized outputs;
use trace-v2/inventory-v2/provenance-v2 and run-records-v2/summary-v2/report-v2.
No additional model call or changed evaluated runtime resulted from this fix.

Next: declare the next paired step/request allowance and recompute reservation
headroom, rebuild and retry 8B before 14B. Keep task/permissions and source pins
unchanged; do not work around the observed path gate by weakening policy.
Final-finish telemetry also needs capture for the next run. Docker cleanup verified.
