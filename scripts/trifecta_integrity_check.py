#!/usr/bin/env python3
"""
Trifecta Integrity Check Hook.
Valida que los archivos de contexto (_ctx/) mantengan su estructura e integridad.
"""

import sys


def check_integrity():
    import subprocess
    import os

    print("   Running deep integrity check via 'trifecta ctx validate'...")
    try:
        # Usamos uv run para asegurar el entorno correcto
        # Set TRIFECTA_NO_TELEMETRY=1 to activate telemetry kill switch (no writes to repo)
        env = os.environ.copy()
        env["TRIFECTA_NO_TELEMETRY"] = "1"
        result = subprocess.run(
            ["uv", "run", "trifecta", "ctx", "validate", "-s", ".", "--telemetry", "off"],
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode == 0:
            print("   ✅ Context integrity verified")
            return 0
        else:
            print("   ❌ Integrity Check FAILED:")
            print(result.stdout)
            print(result.stderr)
            return result.returncode
    except Exception as e:
        print(f"   ❌ Error executing integrity check: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(check_integrity())
