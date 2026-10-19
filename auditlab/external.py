"""Explicit external-tool adapters. Subprocess arguments are never shell strings."""
import os
import re
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from .io import fresh, write, digest

LANGUAGES = {"javascript-typescript", "python", "c-cpp", "java-kotlin", "csharp", "go", "ruby", "rust", "swift"}

def codeql_plan(source, language, out, execute=False):
    source = Path(source).resolve()
    if not source.is_dir() or language not in LANGUAGES:
        raise ValueError("Existing source checkout and supported CodeQL language required")
    out = fresh(out).resolve()
    revision = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    if subprocess.check_output(["git", "-C", str(source), "status", "--porcelain"], text=True).strip():
        raise ValueError("Source checkout must be clean")
    query = {"javascript-typescript": "javascript", "c-cpp": "cpp", "java-kotlin": "java"}.get(language, language)
    commands = [["codeql", "database", "create", str(out / "database"), f"--language={language}", f"--source-root={source}"],
                ["codeql", "database", "analyze", str(out / "database"), f"codeql/{query}-queries:codeql-suites/{query}-security-extended.qls",
                 "--format=sarifv2.1.0", f"--output={out / 'findings.sarif'}"]]
    metadata = {"source_commit": revision, "commands": commands, "executed": False,
        "note": "Run in a disposable analysis environment. Compiled targets may need a recorded custom build command. Pin query packs and CLI before research use."}
    write(out / "plan.json", metadata)
    if execute:
        if not shutil.which("codeql"):
            raise ValueError("CodeQL CLI is not installed; plan.json is available")
        metadata["cli_version"] = subprocess.check_output(["codeql", "version", "--format=json"], text=True)
        for index, command in enumerate(commands):
            started = time.monotonic()
            try:
                with (out / f"command-{index}.log").open("w") as log:
                    process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=3600)
            except (subprocess.TimeoutExpired, OSError) as exc:
                metadata.update(failure_step=index,
                    status="timeout" if isinstance(exc, subprocess.TimeoutExpired) else "error",
                    error=str(exc), failed_step_seconds=time.monotonic()-started)
                write(out / "plan.json", metadata)
                raise ValueError(f"CodeQL step {index} failed; inspect plan.json and its log") from exc
            if process.returncode:
                metadata["failure_step"] = index
                metadata["status"] = "error"
                metadata["exit_code"] = process.returncode
                write(out / "plan.json", metadata)
                raise ValueError(f"CodeQL step {index} failed; inspect its log")
        metadata["executed"] = True
        metadata["status"] = "completed"
        metadata["sarif_sha256"] = digest(out / "findings.sarif")
        write(out / "plan.json", metadata)
    return commands

def docker_command(image, workspace, model, prompt, name, network="none", env_names=(), standalone=False, title=None):
    if not re.fullmatch(r"(?:[\w./:-]+@)?sha256:[0-9a-f]{64}", image):
        raise ValueError("Use an immutable registry digest or local sha256 image ID")
    if network in {"host", "bridge"} or not re.fullmatch(r"[a-zA-Z0-9_.-]+", network):
        raise ValueError("Use none or a dedicated lab network with a controlled model gateway")
    if not model or model.startswith("-") or "REQUIRED" in model:
        raise ValueError("Exact provider/model ID required")
    workspace = Path(workspace).resolve()
    if not workspace.is_dir() or "," in str(workspace):
        raise ValueError("Workspace must be an existing directory without commas")
    command = ["docker", "run", "--rm", "--name", name, "--init", "--read-only", "--cap-drop=ALL",
        "--security-opt=no-new-privileges", "--pids-limit=256", "--memory=4g", "--cpus=2", "--network", network,
        "--user", "1000:1000", "--tmpfs", "/tmp:rw,nosuid,nodev,size=512m,mode=1777",
        "--env", "HOME=/tmp/home", "--workdir", "/work",
        "--mount", f"type=bind,src={workspace},dst=/work"]
    if network != "none":
        # Docker's embedded DNS still resolves same-network service aliases;
        # the explicit loopback resolver prevents forwarding external DNS.
        command += ["--dns", "127.0.0.1"]
    for var in env_names:
        if not re.fullmatch(r"[A-Z][A-Z0-9_]+", var):
            raise ValueError("Invalid environment variable name")
        command += ["--env", var]
    command += ["--entrypoint", "opencode", image, "run"]
    if standalone:
        command += ["--standalone"]
    if title is not None:
        command += ["--title", title]
    command += ["--format", "json", "--model", model, "--", prompt]
    return command

def run_opencode(image, workspace, model, prompt_file, out, network="none", env_names=(), timeout=900, execute=False, standalone=False, title=None):
    if timeout < 1:
        raise ValueError("timeout must be positive")
    out = fresh(out).resolve()
    if out.is_relative_to(Path(workspace).resolve()):
        raise ValueError("Evidence directory must be outside the agent workspace")
    prompt = Path(prompt_file).read_text(encoding="utf-8")
    name = "auditlab-" + uuid.uuid4().hex[:12]
    command = docker_command(image, workspace, model, prompt, name, network, env_names, standalone, title)
    metadata = {"image": image, "model": model, "prompt_sha256": digest(prompt_file), "network": network,
        "command": command, "status": "planned", "timeout_seconds": timeout,
        "oracle_status": "not_collected", "permission_state": "unknown", "standalone": standalone, "title": title,
        "note": "Raw agent output is not trusted oracle evidence. Working tree is modified in place; use a fresh disposable copy per run."}
    write(out / "execution.json", metadata)
    if not execute:
        return metadata
    if not shutil.which("docker"):
        raise ValueError("Docker unavailable; execution.json contains the dry-run plan")
    if any(var not in os.environ for var in env_names):
        raise ValueError("Requested environment variable is missing")
    started = time.monotonic()
    try:
        with (out / "raw.jsonl").open("w") as stdout, (out / "stderr.log").open("w") as stderr:
            proc = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=timeout)
        metadata.update(status="completed" if proc.returncode == 0 else "error", exit_code=proc.returncode)
    except subprocess.TimeoutExpired:
        metadata["status"] = "timeout"
    except OSError as exc:
        metadata.update(status="error", error=str(exc))
    finally:
        metadata["wall_seconds"] = time.monotonic()-started
        write(out / "execution.json", metadata)
        try:
            cleanup = subprocess.run(["docker", "rm", "-f", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
            metadata["cleanup"] = {"status": "command_completed", "exit_code": cleanup.returncode,
                "note": "A nonzero code can mean --rm already removed the container; verify residual state if uncertain."}
        except (subprocess.TimeoutExpired, OSError) as exc:
            metadata["cleanup"] = {"status": "unknown", "error": str(exc), "container_name": name}
        write(out / "execution.json", metadata)
    return metadata
