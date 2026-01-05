#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys
import yaml
from jsonschema import validate

CANONICAL_JOB_STATES = ["pending", "running", "done", "failed"]


def load_yaml(path: Path):
    try:
        return yaml.safe_load(path.read_text())
    except FileNotFoundError:
        return None


def load_json(path: Path):
    return json.loads(path.read_text())


def iter_job_files(root: Path):
    for state in CANONICAL_JOB_STATES:
        job_dir = root / "_ctx" / "jobs" / state
        if not job_dir.exists():
            continue
        for path in sorted(job_dir.glob("*.yaml")):
            if "legacy" in path.parts:
                continue
            yield path


def iter_dod_files(root: Path):
    dod_dir = root / "_ctx" / "dod"
    if not dod_dir.exists():
        return []
    return sorted(p for p in dod_dir.glob("*.yaml") if "legacy" not in p.parts)


def load_schemas(root: Path):
    schema_dir = root / "docs" / "backlog" / "schema"
    return {
        "backlog": load_json(schema_dir / "backlog.schema.json"),
        "work_order": load_json(schema_dir / "work_order.schema.json"),
        "dod": load_json(schema_dir / "dod.schema.json"),
    }


def validate_backlog(root: Path, schemas, strict: bool):
    backlog_path = root / "_ctx" / "backlog" / "backlog.yaml"
    backlog = load_yaml(backlog_path)
    if backlog is None:
        if strict:
            raise FileNotFoundError(f"Missing backlog: {backlog_path}")
        return None
    validate(instance=backlog, schema=schemas["backlog"])
    return backlog


def validate_dod(root: Path, schemas, strict: bool):
    dod_paths = iter_dod_files(root)
    if not dod_paths:
        if strict:
            raise FileNotFoundError("No DoD files found under _ctx/dod")
        return []
    dod_ids = []
    for path in dod_paths:
        dod_data = load_yaml(path)
        if dod_data is None:
            raise FileNotFoundError(f"Missing DoD file: {path}")
        validate(instance=dod_data, schema=schemas["dod"])
        for entry in dod_data.get("dod", []):
            dod_ids.append(entry.get("id"))
    return dod_ids


def validate_jobs(root: Path, schemas, epic_ids, dod_ids):
    for job_path in iter_job_files(root):
        job = load_yaml(job_path)
        if job is None:
            raise FileNotFoundError(f"Missing WO: {job_path}")
        validate(instance=job, schema=schemas["work_order"])
        epic_id = job.get("epic_id")
        dod_id = job.get("dod_id")
        if epic_id not in epic_ids:
            raise ValueError(f"WO {job_path} references unknown epic_id {epic_id}")
        if dod_id not in dod_ids:
            raise ValueError(f"WO {job_path} references unknown dod_id {dod_id}")
        scope = job.get("scope", {})
        if not scope.get("allow") or scope.get("deny") is None:
            raise ValueError(f"WO {job_path} missing scope allow/deny")
        verify = job.get("verify", {})
        commands = verify.get("commands") if isinstance(verify, dict) else None
        if not commands:
            raise ValueError(f"WO {job_path} missing verify.commands")


def main():
    parser = argparse.ArgumentParser(description="Validate backlog + work orders + DoD catalog")
    parser.add_argument("--root", type=str, default=".", help="Repo root")
    parser.add_argument("--fixtures", action="store_true", help="Use tests/fixtures/ctx as root")
    parser.add_argument("--strict", action="store_true", help="Fail on missing canonical files")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if args.fixtures:
        root = (Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "ctx").resolve()

    try:
        schemas = load_schemas(root)
        backlog = validate_backlog(root, schemas, args.strict)
        epic_ids = [e.get("id") for e in backlog.get("epics", [])] if backlog else []
        dod_ids = validate_dod(root, schemas, args.strict)
        validate_jobs(root, schemas, epic_ids, dod_ids)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
