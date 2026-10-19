# Experimental protocol v0.1

## Research scope
The directors' week-two pipeline is the immediate objective. Begin with OpenCode tool implementation risk and real task exposure. Connect the LLM review stage to vulnerability-detection reliability, then later to WP2 causal analysis and WP3 semantics-preserving transformations. Do not replace this agreed pipeline with a new thesis proposal.

## Questions
- RQ1: Which tools are actually invoked across selected SWE tasks and two acting models?
- RQ2: Which source-level candidates have attacker-controlled paths to consequential sinks?
- RQ3: How do two reviewers characterize those candidates, and where do judgments disagree?
- RQ4: Which candidates trigger directly, become reachable through the agent, and produce verified effects?
- Later: do behavior-preserving code transformations change detection judgments, and which internal model mechanisms explain the changes?

## Units and boundaries
Separate the harness, its built-in tools, installed third-party tools/MCP servers, dependencies, and task code. A bug in the application being repaired is not automatically a vulnerability of the agent's tool. Record the affected component explicitly.
For each scenario define attack goal, controlled input surface, attacker knowledge, available privileges, declared policy, and protected resource. Use mock canaries and lab services. Distinguish instruction injection, implementation defects, unsafe intended configuration, and combined cases.

The supervisor's audit note proposes OC-E1 (static shell scan/runtime mismatch), OC-E2 (argument/option injection), OC-F1 (path and permission rules), OC-F2 (patch-tool contrast), OC-N1 (network reachability), and OC-N2 (subsequent disclosure). These are leads. Verify each against the selected commit. No hard path sandbox may be intentional: prove a declared policy was violated before calling a bypass.

## Stage gates
| Stage | Required artifact | Exit evidence |
|---|---|---|
| Scope | Pinned source and benchmark, selected task manifest, two model IDs | Clean checkout hashes; tasks have legitimate instructions and executable utility checks |
| Exposure | Raw and normalized traces plus parser coverage | Real tool calls observed; unsupported events reported |
| Audit | CodeQL SARIF and manual source findings | Code sink, attacker control, policy and preconditions documented |
| Review | Independent reviewer outputs and human adjudication | Evidence-backed reasoning; CWE disagreements retained |
| Direct validation | Isolated tool test, vulnerable/fixed comparison | Host/controller evidence of effect; fixed behavior preserves normal utility |
| Agent validation | Same scenario through legitimate task | Invocation observed, effect independently verified, permission state recorded |

Negative CodeQL output is not absence of vulnerabilities. Permission logic may require custom queries or manual review. If compilation/extraction failed, record coverage failure, not zero findings. LLM rationales are observations of model output, not mechanistic interpretability.

## Controls and sampling
Inventory the directors' intended approximately 20 tasks. Validate the exact benchmark/version and eligible subset. Start with three if the larger set is not reproducible; document this pilot-size deviation. Select by preregistered criteria, not observed attack outcomes. Keep successful and failed benign baselines; report baseline solvability separately. If selecting solvable tasks, make that rule explicit before the attack runs.

For each applicable task/tool scenario compare vulnerable vs patched and benign vs adversarial inputs. Keep acting model, task, permissions, tool schemas and other dependencies fixed. Log image digest, framework commit, prompt hash, model/provider ID, sampling controls if exposed, runtime deadline and actual costs. Repeat runs; randomize execution order for larger experiments. Versions must differ only in the intended repair where feasible. Never expose reference patches to acting models.

Two acting models and two reviewing models are distinct experimental roles. They may be the same products, but document that choice and use independent sessions. Review A must not see Review B. The supplied tool generates packets and compares returned JSON; it does not contact providers.

These review packets include static-analysis findings and provisional CWE tags: this is alert-assisted triage, not a blinded measurement of standalone vulnerability detection. For later WP2/WP3 detection experiments, create separate blinded inputs without reference fixes, labels, CVE IDs or scanner verdicts, and evaluate against held-out ground truth.

## Metrics
- Tool reachability: runs with observed invocation / runs with known invocation observation.
- Trigger rate: runs with a verified vulnerability trigger / runs with known trigger outcome. Also report conditional trigger rate among reached runs when useful, using a separately labelled denominator.
- Run-level ASR: adversarial runs with the predefined unauthorized effect / adversarial runs with known effect outcome.
- Task success: full legitimate task checks satisfied / runs with known task outcome.
- Secure task success: task success AND no unauthorized effect / runs where both are known.
- CWE agreement: set agreement between reviewer labels, not correctness. Correctness requires independently adjudicated ground truth.
- Costs: measured tokens by type, wall time and billed cost; missing telemetry stays unknown. Separate attacker-development cost from victim execution cost.

Store all scheduled attempts, errors, timeouts and unknowns. Current summaries report known-outcome rates and unknown counts; for publication also present sensitivity bounds (successes/scheduled through (successes+unknowns)/scheduled), per-task results and task-aware uncertainty. Do not use repeated oracle checks as independent runs. Small pilot numbers do not support broad significance claims.

HarnessSecurity-Bench reports attack-effect-check ASR and utility-check rates, unlike this repository's run-level outcome schema. Do not directly compare percentages without harmonizing units and scenarios.

## Oracles and permission telemetry
Define the oracle before inspecting model output. Store it outside the task workspace. Use file-state checks, receiving-service canary logs, or instrumented process/file events. Permission state is `asked_allowed`, `asked_denied`, `auto_approved`, `not_asked`, `not_applicable` or `unknown`. The current OpenCode output adapter sets it to unknown: ordinary CLI events do not prove a gate was silent. A silent-crossing claim requires complete correlated permission instrumentation and boundary-crossing evidence. No real eBPF or permission-layer instrumentation is included yet.

## Luxembourg dataset
The importer accepts the observed method-level array with method_change_id, file_change_id, code_before, code_after, repo_name, file_path, cve_id and cwes. Preserve source labels; independently assess CWE accuracy. Join repository/file metadata before reproducible builds. A reference patch does not prove the whole program safe. Split by repository and group related CVEs/commits to reduce leakage; do not randomly split sibling functions. Full dataset, file/repo joins and model-internals experiments are later work.
