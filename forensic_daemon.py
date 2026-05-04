import os
import sys
from pathlib import Path

# Inyectar PYTHONPATH manualmente
root = Path("<REPO_ROOT>/Developer/agent_h/trifecta_dope")
sys.path.insert(0, str(root))

print("--- 🕵️ FORENSIC START ---")
try:
    from src.infrastructure.daemon.runner import DaemonRunner
    print("✅ Import Runner: OK")
    
    # Simular entorno del DaemonManager
    os.environ["TRIFECTA_RUNTIME_DIR"] = str(root / "runtime_test")
    os.environ["TRIFECTA_REPO_ROOT"] = str(root)
    (root / "runtime_test").mkdir(exist_ok=True)
    
    print("⏳ Instantiating from_env()...")
    runner = DaemonRunner.from_env()
    print(f"✅ Instance created. Segment ID: {runner.segment_id}")
    print(f"📍 Socket path: {runner.socket_path}")
    print(f"📍 PID path: {runner.pid_path}")
    
    print("🚀 Attempting to run (single loop check)...")
    # No llamamos a run() porque se bloquea, pero probamos create_server
    from src.infrastructure.daemon.socket_manager import create_server
    server = create_server(runner.socket_path, runner.pid_path)
    print("✅ Server bind: SUCCESS")
    server.close()
    runner.socket_path.unlink()
    runner.pid_path.unlink()
    
    print("--- 🏆 FORENSIC PASS ---")
except Exception as e:
    print(f"❌ CRASH DETECTED: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
