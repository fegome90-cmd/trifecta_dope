import sys
from pathlib import Path

# Path hack: ensure project root is in sys.path for imports
_script_dir = Path(__file__).parent
_project_root = _script_dir.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.infrastructure.lsp_daemon import LSPDaemonClient  # noqa: E402
from src.infrastructure.segment_utils import resolve_segment_root  # noqa: E402

root = resolve_segment_root()
client = LSPDaemonClient(root)

print(f"Connecting to daemon at {root}...")
status = client.send({"method": "status"})
print(f"Status response: {status}")

if status and status.get("status") == "ok":
    state = status.get("data", {}).get("state")
    print(f"Daemon State: {state}")
else:
    print("Failed to get status.")
