import sys
import time
import logging
from pathlib import Path
from src.infrastructure.lsp_client import LSPClient, LSPState

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
