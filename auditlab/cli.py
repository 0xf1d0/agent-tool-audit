"""Command-line entry point. Run python -m auditlab --help."""
import argparse
import json
import shutil
import sys
from . import catalog, demo, evidence, external, gateway, metrics, planning, report

def main():
    parser = argparse.ArgumentParser(description="Coding-agent tool audit research workflow")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor", help="Report optional dependencies; no installation")
    p = sub.add_parser("demo", help="Run local synthetic direct-tool experiment (no LLM)")
    p.add_argument("--out", required=True)
    p = sub.add_parser("select-tasks")
    p.add_argument("--catalog", required=True); p.add_argument("--root", required=True)
    p.add_argument("--count", type=int, default=20); p.add_argument("--out", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--config", required=True); p.add_argument("--out", required=True)
    for command in ("sarif", "normalize-trace", "import-pairs", "summary", "report"):
        p = sub.add_parser(command)
        p.add_argument("--input", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("inventory")
    p.add_argument("--trace", required=True); p.add_argument("--risk", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("review-packets")
    p.add_argument("--findings", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("compare-reviews")
    p.add_argument("--a", required=True); p.add_argument("--b", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("codeql-plan")
    p.add_argument("--source", required=True); p.add_argument("--language", required=True)
    p.add_argument("--out", required=True); p.add_argument("--execute", action="store_true")
    p = sub.add_parser("run-opencode")
    for arg in ("image", "workspace", "model", "prompt", "out"):
        p.add_argument("--" + arg, required=True)
    p.add_argument("--network", default="none"); p.add_argument("--env", action="append", default=[])
    p.add_argument("--timeout", type=int, default=900); p.add_argument("--execute", action="store_true")
    p.add_argument("--standalone", action="store_true", help="Use a private server for OpenCode v2")
    p = sub.add_parser("model-gateway")
    p.add_argument("--config", required=True); p.add_argument("--out", required=True)
    p.add_argument("--model", required=True); p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8080); p.add_argument("--execute", action="store_true")
    p.add_argument("--confirm-free-only", action="store_true")
    a = parser.parse_args()
    try:
        if a.cmd == "doctor":
            value = {"python": sys.version.split()[0], "optional_tools": {name: shutil.which(name) for name in ("git", "docker", "codeql", "opencode", "codex")}}
        elif a.cmd == "demo": value = str(demo.run_demo(a.out))
        elif a.cmd == "select-tasks": value = catalog.select(a.catalog, a.root, a.count, a.out)
        elif a.cmd == "plan": value = {"planned_runs": len(planning.plan(a.config, a.out))}
        elif a.cmd == "sarif": value = {"candidates": len(evidence.ingest_sarif(a.input, a.out))}
        elif a.cmd == "normalize-trace": value = evidence.normalize_opencode(a.input, a.out)
        elif a.cmd == "import-pairs": value = {"pairs": len(evidence.import_pairs(a.input, a.out))}
        elif a.cmd == "summary": value = metrics.summarize(a.input, a.out)
        elif a.cmd == "report": report.report(a.input, a.out); value = {"report": a.out}
        elif a.cmd == "inventory": value = evidence.inventory(a.trace, a.risk, a.out)
        elif a.cmd == "review-packets": evidence.review_packets(a.findings, a.out); value = {"packets": a.out}
        elif a.cmd == "compare-reviews": value = evidence.compare_reviews(a.a, a.b, a.out)
        elif a.cmd == "codeql-plan": value = external.codeql_plan(a.source, a.language, a.out, a.execute)
        elif a.cmd == "run-opencode": value = external.run_opencode(a.image, a.workspace, a.model, a.prompt, a.out, a.network, a.env, a.timeout, a.execute, a.standalone)
        elif a.cmd == "model-gateway": value = gateway.serve(a.config, a.out, a.model, a.host, a.port, a.execute, a.confirm_free_only)
        print(json.dumps(value, indent=2))
    except (ValueError, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")
