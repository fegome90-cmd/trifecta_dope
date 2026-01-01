import sys
import time
from pathlib import Path
from src.infrastructure.lsp_daemon import LSPDaemonClient
from src.infrastructure.segment_utils import resolve_segment_root

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
