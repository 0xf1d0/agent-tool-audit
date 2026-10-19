"""Evidence-labelled portable report, without external dependencies."""
import html
from pathlib import Path
from .io import load

def pct(item):
    if item is None or item["rate"] is None:
        return "not measured"
    return f'{item["passed"]}/{item["known"]} ({item["rate"]:.1%}); unknown={item["unknown"]}'

def report(summary, out):
    data = load(summary)
    body = []
    for group in data["groups"]:
        body.append([group["experiment_mode"], group["model"], group["tool_version"], group["input_kind"],
            str(group["scheduled_runs"]), pct(group["run_level_asr"]), pct(group["task_success"]), pct(group["secure_task_success"])])
    headers = ["Mode", "Model", "Tool version", "Input", "Runs", "Run-level ASR", "Task success", "Secure task success"]
    cells = lambda row, tag: "<tr>" + "".join(f"<{tag}>{html.escape(v)}</{tag}>" for v in row) + "</tr>"
    table = cells(headers, "th") + "".join(cells(row, "td") for row in body)
    page = """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agent Tool Audit — experiment report</title><style>
body{font:16px system-ui,sans-serif;margin:3rem auto;padding:0 1.5rem;max-width:1200px;color:#17253d;background:#f5f7fb}
h1{font-size:2.3rem;margin-bottom:.4rem} .label{color:#116b73;font-weight:700;letter-spacing:.12em}
.note{padding:1rem 1.3rem;background:#fff1cf;border-left:4px solid #bd8512;line-height:1.6}
.wrap{overflow:auto;margin:2rem 0}table{border-collapse:collapse;background:white;width:100%}th,td{text-align:left;padding:.9rem;border-bottom:1px solid #dbe2ec;font-size:14px}th{background:#17253d;color:white}p{line-height:1.65}
</style><p class="label">RESEARCH WORKFLOW / EVIDENCE REPORT</p><h1>Agent Tool Audit</h1>
<p>Tool reachability, unauthorized effects and legitimate task completion.</p>
<div class="note"><b>Interpret the mode before the numbers.</b> synthetic_direct_tool is a deliberately vulnerable local fixture: no LLM, no OpenCode, no CodeQL. It validates measurement plumbing only. A real-agent report requires independently collected runtime evidence.</div>
<div class="wrap"><table>""" + table + """</table></div>
<p>ASR here is run-level and applies only to adversarial inputs. It is not HarnessSecurity-Bench's attack-oracle-level ASR. Unknown verdicts remain visible and are excluded from rate denominators. Secure task success requires task success and no unauthorized effect, with both outcomes known.</p>
<p>Single cases are demonstrations, not generalizable estimates. Costs are not inferred from missing telemetry. See summary.json and runs.jsonl for the underlying records.</p></html>"""
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(page, encoding="utf-8")
