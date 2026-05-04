import os
import sys
from pathlib import Path

# Inyectar PYTHONPATH manualmente
root = Path("<REPO_ROOT>/Developer/agent_h/trifecta_dope")
sys.path.insert(0, str(root))

# Ruta autorizada
safe_runtime = Path("~/.local/share/trifecta/forensic_test").expanduser().resolve()
safe_runtime.mkdir(parents=True, exist_ok=True)

print(f"--- 🕵️ FORENSIC START (Safe Zone: {safe_runtime}) ---")
try:
    from src.infrastructure.daemon.runner import DaemonRunner
    from src.infrastructure.daemon.socket_manager import create_server
    
    os.environ["TRIFECTA_RUNTIME_DIR"] = str(safe_runtime)
    os.environ["TRIFECTA_REPO_ROOT"] = str(root)
    
    print("⏳ Instantiating from_env()...")
    runner = DaemonRunner.from_env()
    print(f"✅ Instance created. Segment ID: {runner.segment_id}")
    
    print(f"🚀 Attempting server bind at: {runner.socket_path}")
    server = create_server(runner.socket_path, runner.pid_path)
    print("✅ Server bind: SUCCESS")
    server.close()
    
    print("--- 🏆 FORENSIC PASS ---")
except Exception as e:
    print(f"❌ CRASH DETECTED: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
