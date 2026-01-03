import sys
import logging
from pathlib import Path

# Path hack: ensure project root is in sys.path for imports
_script_dir = Path(__file__).parent
_project_root = _script_dir.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.infrastructure.lsp_client import LSPClient, LSPState  # noqa: E402

# Configure logging to stdout
logging.basicConfig(level=logging.DEBUG)

root = Path.cwd()
print(f"Root: {root}")

client = LSPClient(root, telemetry=None)
print("Starting LSPClient...")
client.start()

print("Waiting for warmup...")
# Trigger didOpen
test_file = root / "src/infrastructure/cli.py"
if test_file.exists():
    client.did_open(test_file, test_file.read_text())
    print(f"Sent did_open for {test_file}")

for _ in range(10):
    print(f"State: {client.state.name}")
    if client.state == LSPState.READY:
        print("LSPClient READY!")
        break

client.stop()
