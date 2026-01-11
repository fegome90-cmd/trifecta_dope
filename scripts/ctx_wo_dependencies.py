#!/usr/bin/env python3
"""
Work Order dependency analysis and visualization.
"""
import argparse
from collections import defaultdict
from pathlib import Path
import sys
import yaml


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text())


def load_all_wos(root: Path) -> dict:
    """Load all WOs from all states."""
    wos = {}
    for state in ["pending", "running", "done", "failed"]:
        state_dir = root / "_ctx" / "jobs" / state
        if not state_dir.exists():
            continue
        for wo_file in state_dir.glob("WO-*.yaml"):
            wo_data = load_yaml(wo_file)
            wos[wo_data["id"]] = {
                **wo_data,
                "state": state,
                "path": wo_file
            }
    return wos


def main():
    parser = argparse.ArgumentParser(description="Analyze WO dependencies")
    parser.add_argument("--root", default=".", help="Repo root")
    parser.add_argument("--wo-id", help="Specific WO to analyze")
    parser.add_argument("--list-blocking", action="store_true", help="List WOs blocking the specified WO")
    parser.add_argument("--list-blocked", action="store_true", help="List WOs blocked by the specified WO")
    parser.add_argument("--graph", action="store_true", help="Show dependency graph")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    wos = load_all_wos(root)

    if args.graph:
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("   Dependency Graph")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for wo_id, wo_data in sorted(wos.items()):
            deps = wo_data.get("dependencies", [])
            if deps:
                print(f"{wo_id} → {', '.join(deps)}")
        return 0

    if args.wo_id:
        wo_data = wos.get(args.wo_id)
        if not wo_data:
            print(f"ERROR: WO {args.wo_id} not found")
            return 1

        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"   {args.wo_id}: {wo_data.get('title', 'N/A')}")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"Status:      {wo_data['state']}")

        deps = wo_data.get("dependencies", [])
        print(f"\nDirect Dependencies: {len(deps)}")
        for dep in deps:
            dep_state = wos.get(dep, {}).get("state", "unknown")
            status_icon = "✓" if dep_state == "done" else "✗"
            print(f"  {status_icon} {dep} ({dep_state})")

        return 0

    # Default: show all WOs with dependencies
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("   Work Orders with Dependencies")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    for wo_id, wo_data in sorted(wos.items()):
        if wo_data["state"] in ["pending", "running"]:
            deps = wo_data.get("dependencies", [])
            if deps:
                unsatisfied = [d for d in deps if wos.get(d, {}).get("state") != "done"]
                status = "READY" if not unsatisfied else "BLOCKED"
                print(f"\n{wo_id}: {wo_data.get('title', 'N/A')}")
                print(f"  Status: {status} ({wo_data['state']})")
                print(f"  Dependencies: {', '.join(deps)}")
                if unsatisfied:
                    print(f"  Unsatisfied: {', '.join(unsatisfied)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
