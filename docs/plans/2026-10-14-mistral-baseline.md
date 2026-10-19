# Resume first baseline with current sources and Mistral Free mode

## Goal and definition of done

Pin the latest official OpenCode and SkillsBench default-branch commits at fetch
time, curate real eligible tasks, select two current Mistral acting models, and
prepare a disposable runtime, scoped model gateway and explicit permission policy.
Execute a benign baseline only when Docker access, a verified image, credential
and Free-mode availability exist. Preserve the directors' pipeline and later
WP2/WP3 gates. Configuration, planned runs and synthetic tests are not results.

## Authorized inputs and constraints

The user chose latest upstream source repositories, two relevant Mistral models
using free usage only, few available tokens, and creation of missing lab setup.
Use `.venv/bin/python` (3.14.4). OpenCode upstream is
`https://github.com/anomalyco/opencode`; SkillsBench upstream is
`https://github.com/benchflow-ai/skillsbench`. Resolve latest once and pin the
result; do not silently refetch during a trial. Never execute task instructions
or environment scripts on the host.

Proposed actors: Mistral Small 4 and Mistral Medium 3.5, with exact API IDs from
current official documentation and authenticated model-list confirmation before
execution. Reuse the same two products as independent reviewers to limit setup;
review sessions are separate. Neither account access nor free quota is assumed.
No pay-as-you-go usage is authorized. Start with one task × two actors × one
repetition, then expand the three-task pilot if remaining quota permits. The
approximately 20-task inventory target and three-repetition validation design
remain visible; the smaller baseline is a declared quota-limited smoke stage.

## Steps

1. **Done:** reread STATUS/PROTOCOL/RUNBOOK and planning/runtime skills. Docker
   client is installed but socket access fails even outside the sandbox; sudo
   requires authentication. CodeQL 2.27.2 found at `/opt/codeql/codeql`.
2. **Done:** downloaded clean latest sources; OpenCode
   `943dc005f792d401b0dd24dd965082bdcb3a5f09` and SkillsBench
   `f860ecf02ef53412a030f8661c83d644b739ff01`; inspected task metadata/verifiers.
3. **Done:** CLI reports nine statically eligible tasks, not 20. Three selected
   in declared order: dialogue-parser, fix-build-agentops, fix-build-google-auto.
   Runtime reproducibility has not been established.
4. **Done preparation:** hashed baseline metadata, sanitized dialogue input,
   independent verifier recipe and archived pinned source. Upstream verifier's
   missing parse_script coverage is recorded; full task success stays unknown.
5. **Done implementation, live unverified:** fixed-upstream model gateway with scoped token,
   two-model allowlist, request/output/total quota limits and trusted usage log.
   Agent containers get only a per-session gateway token, never the Mistral key.
6. **Done preparation; build blocked:** digest-pinned base images, v2 policy and
   actor/verifier/gateway build targets, controller driver and network probes.
   Actual image build failed on Docker socket permission; no image exists.
7. **Done:** 45 unit tests, compile, CLI selection, fresh synthetic demo/inventory/
   report and dry-run checks. Updated STATUS and `docs/MISTRAL_BASELINE.md`.

## Validation and evidence

Use a fresh `artifacts/mistral-baseline-prep-001/` bundle. Preserve prior evidence.
Record commands/return codes, clean source commits, task hashes, actual model IDs,
policy/build hashes and budget. Required Python check:
`.venv/bin/python -m unittest discover -s tests -v`.
Gateway tests must exercise unauthorized requests, model/path allowlists, quota
exhaustion, missing usage and schema drift; adapter tests must protect evidence
and reject invalid runtime metadata. Synthetic tests do not establish real
network isolation or provider compatibility.

## Blockers and next executable action

Current host blockers: Docker socket permission still fails after authorization;
key now authenticates both selected IDs on GET /v1/models, but `.env` Free-only
confirmation flag is false and remaining model limits are unknown. No completion
was requested. Verify host Docker access and Free mode, build to a fresh evidence
directory using the resolved digests, verify v2 CLI/config, then execute the first
benign trial as documented in `docs/MISTRAL_BASELINE.md`. CodeQL still needs its
documented disposable analysis environment; no scan was run on the host.
