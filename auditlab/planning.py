"""Deterministic, explicitly unexecuted experiment matrices."""
from itertools import product
import hashlib
import json
from .io import load, write

def plan(config, out):
    cfg = load(config)
    if not cfg.get("tasks") or not cfg.get("models"):
        raise ValueError("Select tasks and exact model IDs first")
    if len(cfg["models"]) != 2 or len(set(cfg["models"])) != 2:
        raise ValueError("The pilot requires two distinct acting models")
    if type(cfg.get("repetitions")) is not int or cfg["repetitions"] < 1:
        raise ValueError("repetitions must be positive")
    if len(set(cfg["tasks"])) != len(cfg["tasks"]):
        raise ValueError("Duplicate task IDs")
    if cfg.get("versions") != ["vulnerable", "patched"] or cfg.get("inputs") != ["benign", "adversarial"]:
        raise ValueError("Use the four controlled version/input combinations")
    if any("REQUIRED" in str(v) for v in cfg.values()):
        raise ValueError("Resolve REQUIRED placeholders before scheduling")
    rows = []
    for task, model, version, inp, rep in product(cfg["tasks"], cfg["models"], cfg["versions"], cfg["inputs"], range(cfg["repetitions"])):
        identity = [task, model, version, inp, rep, cfg]
        rows.append({"run_id": hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:16],
            "task_id": task, "model": model, "tool_version": version, "input_kind": inp,
            "repetition": rep+1, "status": "not_run"})
    write(out, {"config": cfg, "planned_runs": len(rows), "runs": rows})
    return rows
