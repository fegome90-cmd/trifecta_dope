import yaml
from pathlib import Path


def patch_wo(path):
    with open(path) as f:
        try:
            data = yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading {path}: {e}")
            return

    if data is None:
        return

    changed = False

    if "version" not in data:
        data["version"] = 1
        changed = True

    if "verify" not in data or not data.get("verify", {}).get("commands"):
        if "verify" not in data:
            data["verify"] = {"commands": []}
        elif not isinstance(data["verify"], dict):
            data["verify"] = {"commands": []}
        elif "commands" not in data["verify"]:
            data["verify"]["commands"] = []

        # Try to infer commands from x_micro_tasks if present
        if not data["verify"]["commands"] and "x_micro_tasks" in data:
            for task in data["x_micro_tasks"]:
                if task.get("status") == "done" and task.get("commands"):
                    data["verify"]["commands"].extend(task["commands"])
                    break

        if not data["verify"]["commands"]:
            data["verify"]["commands"] = ["# No verification command provided (Legacy WO)"]

        changed = True

    if "scope" not in data:
        data["scope"] = {"allow": [], "deny": []}
        changed = True

    if "execution" not in data:
        data["execution"] = {"engine": "trifecta", "required_flow": ["verify"], "segment": "."}
        changed = True

    if changed:
        print(f"Patching {path}")
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)


for path in Path("_ctx/jobs").rglob("*.yaml"):
    if "legacy" in path.parts:
        continue
    patch_wo(path)
