import time
import sys
from pathlib import Path
from src.infrastructure.lsp_client import LSPClient


def probe_ready():
    root = Path.cwd()
    print(f"Probing LSP in {root}...")

    # Mock telemetry
    class MockTelemetry:
        def event(self, *args, **kwargs):
            print(f"[Telemetry] event: {args} {kwargs}")

        def incr(self, *args):
            print(f"[Telemetry] incr: {args}")

    client = LSPClient(root, MockTelemetry())
    client.start()

    print("Client started. Waiting for READY...")

    # Wait up to 5 seconds
    for i in range(50):
        if client.is_ready():
            print("SUCCESS: LSP is READY.")
            return
        time.sleep(0.1)

    print("FAILURE: LSP did not become READY in 5 seconds.")
    print(f"Final State: {client.state}")


if __name__ == "__main__":
    probe_ready()
