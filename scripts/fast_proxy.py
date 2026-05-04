import socket
import json
import time
import sys
import hashlib
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: fast_proxy.py <query>")
        sys.exit(1)
        
    query = sys.argv[1]
    
    # 1. Proxy Startup
    t0 = time.time()
    repo_path = Path(".").resolve()
    repo_hash = hashlib.sha256(str(repo_path).encode()).hexdigest()[:12]
    socket_path = f"/tmp/trifecta_f1_{repo_hash}.sock"
    
    # 2. Connect & Request
    t1 = time.time()
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(2.0)
            s.connect(socket_path)
            
            request = {
                "jsonrpc": "2.0",
                "id": int(time.time() * 1000),
                "method": "tools/call",
                "params": {
                    "name": "ctx_oracle",
                    "arguments": {
                        "query": query,
                        "k": 5
                    }
                }
            }
            
            t2 = time.time()
            s.sendall(json.dumps(request).encode() + b"\n")
            
            # 3. Receive
            data = b""
            while True:
                chunk = s.recv(4096)
                if not chunk: break
                data += chunk
                if b"\n" in data: break
                
            t3 = time.time()
            response = json.loads(data.decode())
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
        
    t4 = time.time()
    
    if "result" in response and "content" in response["result"]:
        content = response["result"]["content"][0]["text"]
        payload = json.loads(content)
        metadata = payload.get("metadata", {})
        daemon_ms = metadata.get("latency_ms", 0)
        timings = metadata.get("timings", {})
        
        # Calculate breakdowns
        startup_ms = (t1 - t0) * 1000
        connect_ms = (t2 - t1) * 1000
        transport_roundtrip_ms = (t3 - t2) * 1000
        decode_ms = (t4 - t3) * 1000
        total_ms = (t4 - t0) * 1000
        
        overhead_ms = transport_roundtrip_ms - daemon_ms
        
        print(f"--- Fast Proxy Performance ---")
        print(f"Total Client Time   : {total_ms:.2f} ms")
        print(f"├─ Proxy Startup    : {startup_ms:.2f} ms")
        print(f"├─ Socket Connect   : {connect_ms:.2f} ms")
        print(f"├─ Socket Roundtrip : {transport_roundtrip_ms:.2f} ms")
        print(f"│  ├─ Daemon Inside : {daemon_ms:.2f} ms")
        print(f"│  │  ├─ Pack Load  : {timings.get('pack_load_and_search_ms', 0):.2f} ms")
        print(f"│  │  ├─ AST Resol  : {timings.get('ast_resolution_ms', 0):.2f} ms")
        print(f"│  │  └─ LSP Signal : {timings.get('lsp_signal_ms', 0):.2f} ms")
        print(f"│  └─ Socket/OS Wait: {overhead_ms:.2f} ms")
        print(f"└─ Decode/Render    : {decode_ms:.2f} ms")
        print(f"------------------------------")
    else:
        print("Invalid response")
        print(response)

if __name__ == "__main__":
    main()
