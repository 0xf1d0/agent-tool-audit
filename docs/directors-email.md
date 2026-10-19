Subject: Week-two research pipeline: implementation plan and lessons from HarnessSecurity-Bench

Dear all,

Following the pipeline you proposed during my second week, I have started organizing the experimental workflow around OpenCode, software-engineering tasks from SkillsBench, and two LLMs.

My understanding of the sequence is to observe which tools the agents use, prioritize the tools with the greatest potential security impact, analyze their implementations with CodeQL, and have the resulting vulnerability/CWE candidates reviewed by LLMs.

I will distinguish the models' two roles: performing the coding tasks and reviewing the tool vulnerabilities. After review, I propose validating selected candidates through direct tool execution and then through agent execution, using vulnerable/patched comparisons and independent checks of both security effects and task completion. This would establish whether a candidate weakness is actually reachable and consequential, rather than relying only on a static alert or an LLM judgment.

This initial study can connect to the broader thesis objectives by providing concrete cases for studying the reliability of LLM vulnerability assessments, followed by robustness experiments and mechanistic analysis.

HarnessSecurity-Bench offers a useful reference. It evaluates 23 tasks across five attack surfaces and six coding-agent harnesses, using GLM-5.2 as the acting model. Its main findings include:

- Auto-approval increased attack success from 29.2% to 95.6%, while utility increased from 77.1% to 95.4%.
- Network isolation reduced attack success from 57.1% to 0.8%, but utility decreased from 90.9% to 66.4%.
- Command allowlisting reduced attack success from 98.1% to 50.0%, with a smaller utility decrease from 99.2% to 97.7%.

These are separate mechanism-specific comparisons. The paper measures successful attack-effect checks, rather than the percentage of compromised runs; its auto-approval comparison uses an automated permission reviewer. It reports 2,500 trials, 81,155 tool calls, approximately 2.218 billion recorded tokens and 589.32 cumulative execution hours, but no monetary cost per successful attack. OpenCode is not among its six runtime-evaluated harnesses.

For next week's discussion, I have prepared a repository with the workflow tooling, Codex instructions, experiment templates and a runnable local demonstration. The demonstration uses a deliberately vulnerable fixture; it is not a result about OpenCode. The real experiments still require pinned framework/task versions, the two model choices and the execution environment.

I will keep the approximately twenty-task target, while first validating a small pilot. The exact SkillsBench version needs checking: the current v1.1 registry lists sixteen Software Engineering tasks, nine of which are easy or medium.

Best regards,
François
