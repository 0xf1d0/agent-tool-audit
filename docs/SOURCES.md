# Sources and interpretation

Documentation checked on 2026-10-14; pin concrete versions before experiment execution.

## Research context supplied by the researcher (not redistributed)
- *PhD Thesis: Mechanistic Interpretability and Problem-Space Adversarial Attacks for LLM-based Software Vulnerability Detection*: WP2 and WP3 objectives.
- *OpenCode Tool Vulnerability Audit*, Oct 5, 2026: two-factor model (code sink × agent reachability), direct-tool then agent-in-the-loop validation, permission telemetry and version-specific candidate leads. Its product-specific assertions require independent verification.
- Luxembourg method-level sample: field mapping only. Source CWE labels are not independently verified.

## Public research
- Zhu et al., *HarnessSecurity-Bench: Do Security Mechanisms Really Protect Coding Agent Harnesses?*, arXiv:2610.07639v1, 6 Oct 2026. https://arxiv.org/abs/2610.07639
  The uploaded preprint reports 23 tasks, six runtime harnesses, one acting model (GLM-5.2), 2,500 trials, 81,155 calls, about 2.218 billion recorded tokens, and 589.32 cumulative execution hours. AA-OFF uses Qwen3.8-27B for permission review. ASR and utility are oracle-check rates, not whole-run rates. No monetary cost per successful attack is established. OpenCode is not in the six-harness runtime evaluation.
- SkillsBench registry: https://www.thebenchmark.company/tasks
  The viewed v1.1 registry listed 16 SWE tasks: 3 easy, 6 medium and 7 hard. This observation is version-specific; inspect the selected commit rather than assuming 20 eligible tasks.
- SkillsBench source: https://github.com/benchflow-ai/skillsbench

## Implementation references
- OpenCode CLI: https://opencode.ai/docs/cli/ — `run --format json --model provider/model`. Event schema is treated as version-dependent and must be tested on the pinned build.
- CodeQL analysis: https://docs.github.com/en/code-security/tutorials/customize-code-scanning/analyze-code
- CodeQL language support: https://codeql.github.com/docs/codeql-overview/supported-languages-and-frameworks/
- Codex skills: https://developers.openai.com/codex/skills/
- Codex AGENTS.md: https://developers.openai.com/codex/guides/agents-md/
- Codex command rules: https://developers.openai.com/codex/rules/

No external benchmark data or third-party source code is embedded in the synthetic fixtures.
