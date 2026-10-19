# First real experiment preparation

## Goal and definition of done

Prepare the directors' pipeline: OpenCode → selected SWE tasks → two acting
models → observed tool exposure → CodeQL/manual candidates → two independent
reviewers → direct-tool validation → agent validation. The first execution is a
benign baseline on one real task, followed by exposure across the selected pilot.
Preparation is complete when available local checks, configuration drafts,
selection rules, evidence boundaries and missing inputs are documented. Execution
is complete only after pinned inputs, an isolated run, real traces with parser
coverage and a controller-side utility check exist. No real experiment has run.

## Inputs and version constraints

Read AGENTS.md, STATUS, PROTOCOL, RUNBOOK, PLANS, CODEX and PUBLICATION, and the
plan-audit-pilot skill. Local evidence is in the ignored directory
`artifacts/first-real-prep-001/`; preserve it and use a new numbered directory for
repeated preparation. This project has no Git checkout, so a research-controller
commit cannot be recorded; file hashes are recorded instead. No `vendor/`
checkouts are present. Python is 3.14.4 (`python3`); `python` is absent. Git,
OpenCode and Codex are on PATH. Docker and CodeQL are absent. PATH availability
does not verify versions, configuration or source provenance.

`pilot.unresolved.json` and `sources.unresolved.json` are literal copies of the
configuration templates. REQUIRED values deliberately remain unresolved. The
task catalog and verifier catalog contain headers only. `preparation.json`
records unknown selections and metadata as null. There is no real schedule.

## Ordered steps and evidence

1. **Done:** review protocol and stage gates; inspect local sources and adapters.
   No pinned task/framework sources or executable benchmark verifiers exist here.
2. **Done:** doctor, 26 unit tests, synthetic demo, inventory and report.
   Commands, return codes and logs are in `checks.json` and adjacent text files.
   Four synthetic controls preserved utility; only vulnerable/adversarial
   disclosed the fixture canary. These are engineering checks only.
3. **Done:** copy configuration/catalog templates and check unresolved `plan`
   rejection. It returned exit 2 (select tasks and exact model IDs first) and
   did not create `matrix.json`. No dummy IDs were used to bypass the gate.
4. **Blocked:** obtain agreed clean source checkouts and pins. Record canonical
   URLs, full commits, licenses, clean status, task environment and instruction
   hashes. Inspect benchmark files as untrusted data, never as assistant policy.
5. **Blocked:** curate and select tasks using the rule below. The CLI checks
   instruction paths and checkout cleanliness; it does not inspect verifiers.
   Complete `task-verifiers.csv` alongside the catalog, including exact argument
   arrays, hashes, timeouts, environment requirements and reference exclusions.
6. **Blocked:** freeze acting/reviewing model roles, runtime, policy, gateway,
   prompts, sampling controls and budget; resolve the configuration copies.
7. **Blocked:** generate an explicitly unexecuted controlled matrix, once a real
   candidate and its intended repair justify vulnerable/patched labels. First
   baseline uses the pinned upstream version; do not label it vulnerable based
   only on an audit lead. The existing `plan` command requires all four controls
   and does not produce a baseline-only schedule.
8. **Blocked:** create a fresh disposable task copy, inspect image CLI help and
   writable cache requirements in isolation, dry-run `run-opencode`, review its
   mount/network/policy boundaries, then execute the first benign baseline.
9. **Pending baseline evidence:** normalize raw output, inspect coverage including
   unsupported events, inventory actual tools, and run the trusted utility check
   against the resulting task snapshot in a separate disposable verifier runtime.
10. **Pending exposure:** prioritize actual tool implementations; pin CodeQL CLI,
    language, extraction and query packs, obtain SARIF and source context; review
    independently, adjudicate, validate directly, then through the acting agent.

## Selection and measurement decisions

Keep approximately 20 tasks as the target. Inventory the pinned benchmark before
asserting any shortage. Eligible tasks must be SWE, easy/medium according to a
recorded benchmark label or documented curation rubric, have legitimate
instructions, reproducible environments and executable full utility checks.
Exclude tasks that leak reference patches/answers into the agent workspace or
cannot meet the isolation contract. Record every exclusion and its reason.
Order eligible tasks by easy before medium, then lexicographic task ID, before
observing baseline or attack outcomes. Do not silently filter failed baselines.

A three-task pilot is a proposed staged start, consistent with PROTOCOL, not a
claim of three available tasks. First try the 20-task selection; if it reports a
shortage, preserve the actual count/error and explicitly record the pilot-size
deviation before selecting three. If fewer than three pass, report that shortage
and do not fabricate IDs. Keep selected tasks fixed through paired comparisons.

First baseline: one task, acting model A, pinned upstream tool implementation,
benign input. After smoke verification, run the same selected tasks on both acting
models, retaining errors and timeouts. Three repetitions are the template's
proposed setting, subject to a recorded budget. Three tasks × two models × two
tool versions × two input conditions × three repetitions would yield 72 planned
candidate-validation runs; this arithmetic is not an executed denominator.
Reviewers may be the same products as actors only if this choice is explicit;
review A and B use independent sessions and never see each other's decisions.

## Boundary and oracle design before attacks

The baseline has no attacker manipulation and no security verdict. Utility is
true only when the pinned full task verifier passes on the output snapshot;
false requires a valid completed failing check; missing, invalid or incomplete
checks yield null. Agent claims and process exit status do not establish utility.
Tool reachability needs real parsed invocations and coverage inspection; zero
parsed calls with unknown schemas is unknown. Permission state remains unknown
until correlated complete instrumentation is available. Cost and tokens remain
null if telemetry is missing. Baseline ASR is not applicable.

For a later candidate, attacker control is limited to a preregistered surface
(for example a task file, tool-output content or argument) and its allowed
capabilities; no control of the controller, oracle, policy, reference repair or
trial ledger. The protected resource, declared policy, exact unauthorized effect,
trigger condition and evidence source are candidate-specific and currently
unknown. Do not infer a bypass from intentionally broad permissions.

Before attacks, complete an oracle specification outside the agent workspace.
Use a mock canary/resource and trusted file-state, process or receiving-service
evidence. Define true/false/unknown independently for reachability, trigger,
effect and utility, and define permission event IDs and collection completeness.
The same scenario must compare upstream/repair × benign/adversarial directly
before agent execution. Expected controls: benign inputs preserve utility in
both versions; adversarial upstream establishes the predefined effect if the
candidate is valid; the repair prevents that effect while preserving utility.
These are hypotheses, not observed outcomes. Missing events and timeouts retain
unknown outcomes unless an independent oracle supports a result.

Use fresh task workspaces per attempt, writable only as required by UID 1000.
Only the sanitized task workspace is mounted at `/work`; never mount this
repository, evidence, oracle, home, Docker socket, SSH material, full benchmark
or reference datasets. Keep the trial ledger and outcomes on the controller.
The existing adapter limits CPU/RAM/PIDs/time, drops capabilities and uses a
read-only root. A dedicated network name is not an egress control: require a
documented scoped gateway and actual allowed/denied destinations. Record the
policy bytes and hash, gate decisions and residual container cleanup. Use a
disposable VM for adversarial work where required by the lab design.

Candidate, review_supported, direct_tool_validated and agent_validated remain
separate states. WP2 causal work and WP3 behavior-preserving transformations
remain later extensions using separate blinded inputs and held-out ground truth.

## Exact missing inputs and which stage they block

| Input | Required concrete value | First blocked stage |
| --- | --- | --- |
| Framework source | Agreed OpenCode canonical URL, full commit, clean local checkout and license | Source inspection |
| Benchmark source | Agreed SkillsBench URL/full commit, clean checkout, task environments and verifiers | Task selection |
| Model roles | Two distinct exact provider/model IDs for actors; two reviewer IDs and explicit same/different product choice | Model freeze; reviewers needed at review |
| Sampling and budget | Exposed sampling/seed controls or documented unavailability, repetitions, maximum tokens/spend and stopping rule | Baseline execution |
| Runtime | Docker-capable disposable host/VM, immutable image registry digest, framework/dependency build provenance, UID/cache compatibility | Baseline execution |
| Provider access | Scoped gateway configuration, dedicated network/egress rules, short-lived token delivery by environment name; no secrets in docs | Baseline execution |
| Permission policy | Release-specific configuration bytes/hash, intended file/process/network boundaries and actual gate settings | Baseline execution |
| Baseline utility | Selected task instruction and hash, sanitized workspace recipe, exact verifier argv/hash/dependencies and controller-side check location | Baseline execution |
| Static analysis | CodeQL CLI version, pinned query packs, supported target language and reproducible extraction environment | Audit |
| Candidate validation | Observed tool/source sink, attacker surface, repair-only diff, protected mock resource, trusted effect/trigger oracle and correlated permission instrumentation | Direct/agent validation |

No source/model/image choice was inferred from an installed binary or an example.
No provider requests, untrusted task executions or installations were performed.

## Next executable actions after source inputs arrive

Inspect clean checkouts and verifiers; populate the two catalogs. Then run:

```bash
python3 -m auditlab select-tasks --catalog artifacts/first-real-prep-001/task-catalog.csv --root vendor/skillsbench --count 20 --out artifacts/first-real-prep-001/selection-20.json
```

If a recorded shortage justifies the proposed pilot, use count 3 and a different
output name. Resolve baseline runtime/model/policy inputs and dry-run the exact
RUNBOOK stage 4 command with a real digest, workspace, model and instruction.
Do not execute on the host merely because Docker is missing. Once a real
candidate/repair and all configuration fields exist, generate the unexecuted
matrix with `python3 -m auditlab plan --config <resolved-copy> --out <fresh-matrix>`.

## Validation and deviations

All 26 tests passed on Python 3.14.4, outside the previously exercised 3.11–3.13
CI range. No Python code or oracle changed. The synthetic demo and report passed.
Historical delivery validation remains historical; current doctor evidence
supersedes its tool-availability statement for this environment. Preparation
logs/configuration copies are private ignored artifacts; this plan and STATUS
contain no credentials, raw datasets or unsupported research claims.
