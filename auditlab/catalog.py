"""Explicit task selection; never silently manufacture benchmark tasks."""
import csv
import subprocess
from pathlib import Path
from .io import write, digest

REQUIRED = {"task_id", "domain", "difficulty", "task_path", "selection_reason"}

def select(catalog, root, count, out):
    root = Path(root).resolve()
    if count < 1:
        raise ValueError("count must be positive")
    revision = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if subprocess.check_output(["git", "-C", str(root), "status", "--porcelain"], text=True).strip():
        raise ValueError("Benchmark checkout must be clean for reproducible selection")
    with open(catalog, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not REQUIRED <= set(reader.fieldnames or []):
            raise ValueError(f"Catalog requires columns {sorted(REQUIRED)}")
        rows = list(reader)
    ids = [r["task_id"] for r in rows]
    if len(ids) != len(set(ids)) or any(not i for i in ids):
        raise ValueError("Task IDs must be nonempty and unique")
    eligible = [r for r in rows if r["domain"] == "software-engineering" and r["difficulty"] in {"easy", "medium"}]
    if len(eligible) < count:
        raise ValueError(f"Requested {count}; only {len(eligible)} eligible tasks. Change scope explicitly.")
    selected = []
    for row in eligible[:count]:
        p = (root / row["task_path"]).resolve()
        if not p.is_relative_to(root) or not p.is_file():
            raise ValueError(f"Task instruction must be a file inside checkout: {row['task_path']}")
        if not row["selection_reason"].strip():
            raise ValueError("Record a selection reason for every task")
        selected.append({**row, "instruction_sha256": digest(p)})
    result = {"schema_version": 1, "benchmark_commit": revision, "catalog_sha256": digest(catalog), "tasks": selected}
    write(out, result)
    return result
