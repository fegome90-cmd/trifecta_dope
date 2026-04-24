import json
import sys
import time
import threading
import socket
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from enum import Enum

# Path configuration for portability
from src.domain.models import TrifectaConfig
from src.domain.result import Ok, Err
from src.application.ast_parser import SkeletonMapBuilder
from src.application.graph_service import GraphService
from src.application.graph_indexer import GraphIndexer
from src.application.plan_use_case import PlanUseCase
from src.application.oracle_use_case import SearchOracleUseCase
from src.application.calibration_use_case import AutonomousWeightCalibrationUseCase
from src.application.discovery_service import EngramDiscoveryService
from src.infrastructure.factories import get_ast_cache
from src.infrastructure.templates import TemplateRenderer
from src.infrastructure.file_system import FileSystemAdapter
from src.infrastructure.telemetry import Telemetry
from src.application.search_get_usecases import SearchUseCase, GetChunkUseCase
from src.application.use_cases import CreateTrifectaUseCase, BuildContextPackUseCase

class ServerState(Enum):
    READY = "READY"
    SYNCING = "SYNCING"
    FAILED = "FAILED"

class TrifectaF1Server:
    """High-performance in-process MCP server for Trifecta."""

    def __init__(self, repo_path: str, sync_mode: str = "auto", build_timeout: int = 30):
        self.repo_path = Path(repo_path).resolve()
        self.sync_mode = sync_mode
        self.build_timeout = build_timeout
        self.state = ServerState.SYNCING
        self.last_error: Optional[str] = None
        
        # Initialize Core Services
        self.telemetry = Telemetry(self.repo_path, level="lite")
        self.fs = FileSystemAdapter()
        self.template_renderer = TemplateRenderer()
        self.discovery = EngramDiscoveryService()
        
        # UseCases
        self.search_uc = SearchUseCase(self.fs, self.telemetry)
        self.get_uc = GetChunkUseCase(self.fs, self.telemetry)
        self.build_uc = BuildContextPackUseCase(self.fs, self.telemetry)
        self.create_uc = CreateTrifectaUseCase(self.template_renderer, self.fs)
        self.plan_uc = PlanUseCase(self.fs, self.telemetry)
        
        # AST Engine
        self.ast_cache = get_ast_cache(persist=True, segment_id=str(self.repo_path), telemetry=self.telemetry)
        self.ast_builder = SkeletonMapBuilder(cache=self.ast_cache, segment_id=str(self.repo_path))
        
        # Graph Engine
        self.graph_service = GraphService()
        self.graph_indexer = GraphIndexer()

        # Oracle (Signal Fusion) — graph_service wired for relational queries
        self.oracle_uc = SearchOracleUseCase(self.ast_builder, telemetry=self.telemetry, graph_service=self.graph_service)
        self.calib_uc = AutonomousWeightCalibrationUseCase(self.fs, self.telemetry)
        
        # Performance Tracking (F1 metrics)
        self.search_count = 0
        self.hit_count = 0
        self.start_time = datetime.now(timezone.utc)
        
        self.max_output_chars = 200000
        self._lock = threading.Lock()

    def _log_error(self, msg: str):
        print(f"[F1-ERROR] {msg}", file=sys.stderr, flush=True)

    def _respond_tool(self, req_id: Any, result: Any):
        """Default MCP response (stdio)."""
        text = json.dumps(result, ensure_ascii=False)
        if len(text) > self.max_output_chars:
            text = text[:self.max_output_chars] + "... [TRUNCATED]"
        
        payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": text}]
            }
        }
        print(json.dumps(payload, ensure_ascii=False), flush=True)

    def _respond_error(self, req_id: Any, code: int, message: str, data: Optional[Dict] = None):
        payload = {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}
        if data: payload["error"]["data"] = data
        print(json.dumps(payload, ensure_ascii=False), flush=True)

    def _get_tool_definitions(self):
        return [
            {"name": "ctx_search", "description": "F1 Search", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}}},
            {"name": "ctx_get", "description": "F1 Retrieval", "inputSchema": {"type": "object", "properties": {"ids": {"type": "array"}}}},
            {"name": "ctx_oracle", "description": "F1 Unified Oracle (LSP+AST+PRIME)", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}}},
            {"name": "ctx_calibrate", "description": "F1 Autonomous Calibration", "inputSchema": {"type": "object", "properties": {"dataset_path": {"type": "string"}}}},
            {"name": "ctx_init", "description": "F1 Bootstrap", "inputSchema": {"type": "object", "properties": {}}},
            {"name": "ast_analyze", "description": "F1 AST", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}}},
            {"name": "ctx_health", "description": "F1 Health", "inputSchema": {"type": "object", "properties": {}}},
        ]

    def _handle_tool_call(self, req_id: Any, params: Dict, responder=None):
        responder = responder or self._respond_tool
        name = params.get("name")
        args = params.get("arguments", {})
        
        if self.state == ServerState.SYNCING and name != "ctx_health":
            self._respond_error(req_id, -32000, "Server is currently syncing/building context pack.", data={"state": self.state.value})
            return

        if self.state == ServerState.FAILED and name != "ctx_health":
            error_msg = f"Server is in FAILED state: {self.last_error}"
            self._respond_error(req_id, -32000, error_msg, data={"state": self.state.value, "recommendation": "Run 'trifecta sync' manually."})
            return

        try:
            if name == "ctx_search":
                with self._lock:
                    self.search_count += 1
                res = self.search_uc.execute(self.repo_path, args.get("query", ""), limit=args.get("k", 5), enable_lint=args.get("enable_lint", False))
                responder(req_id, res)
                if "hits" in res.lower():
                    with self._lock:
                        self.hit_count += 1
            elif name == "ctx_get":
                res = self.get_uc.execute(self.repo_path, args.get("ids", []), mode=args.get("mode", "excerpt"), budget_token_est=args.get("budget_token_est", 1500), max_chunks=args.get("max_chunks"), stop_on_evidence=args.get("stop_on_evidence", False), query=args.get("query"))
                responder(req_id, res)
            elif name == "ctx_oracle":
                with self._lock:
                    self.search_count += 1
                res = self.oracle_uc.execute(self.repo_path, args.get("query", ""), k=args.get("k", 5))
                if isinstance(res, Ok):
                    if len(res.value.prime_chunks) > 0:
                        with self._lock:
                            self.hit_count += 1
                    responder(req_id, res.value.model_dump())
                else:
                    self._respond_error(req_id, -32603, str(res.error))
            elif name == "ctx_calibrate":
                res = self.calib_uc.execute(self.repo_path, Path(args.get("dataset_path", "docs/plans/t9_plan_eval_tasks.md")))
                if isinstance(res, Ok):
                    responder(req_id, res.value)
                else:
                    self._respond_error(req_id, -32603, str(res.error))
            elif name == "ctx_init":
                config = TrifectaConfig(segment=self.repo_path.name, scope="Bootstrap", repo_root=str(self.repo_path))
                self.create_uc.execute(config, self.repo_path, [])
                self.build_uc.execute(self.repo_path)
                responder(req_id, "✅ Done.")
            elif name == "ast_analyze":
                res = self.ast_builder.build(self.repo_path / args["path"])
                responder(req_id, {"symbols": [s.name for s in res.symbols]})
            elif name == "ctx_health":
                engram = self.discovery.discover()
                hit_rate = round(self.hit_count / self.search_count, 2) if self.search_count > 0 else 0.0
                uptime_sec = int((datetime.now(timezone.utc) - self.start_time).total_seconds())
                pack_path = self.repo_path / "_ctx" / "context_pack.json"
                stale_days, chunk_count = 0, 0
                if pack_path.exists():
                    stale_days = max(0, int((time.time() - pack_path.stat().st_mtime) / 86400))
                    try:
                        with open(pack_path) as f: chunk_count = len(json.load(f).get("chunks", []))
                    except: pass
                    
                from src.application.context_service import ContextService
                cache_stats = ContextService.get_cache_stats()
                
                responder(req_id, {
                    "state": self.state.value, "engram_detected": engram.detected,
                    "hit_rate": hit_rate, "search_count": self.search_count,
                    "hits_found": self.hit_count, "uptime_seconds": uptime_sec,
                    "stale_days": stale_days, "chunk_count": chunk_count, "mode": self.sync_mode,
                    "cache_stats": cache_stats
                })
            else:
                self._respond_error(req_id, -32601, f"Unknown tool: {name}")
        except Exception as e:
            self._respond_error(req_id, -32603, str(e))

    def _sync_background(self):
        try:
            pack_path = self.repo_path / "_ctx" / "context_pack.json"
            if self.sync_mode == "auto" or not pack_path.exists():
                res = self.build_uc.execute(self.repo_path)
                if isinstance(res, Err): raise Exception(f"Build failed: {res.error}")
            self.state = ServerState.READY
        except Exception as e:
            self.state = ServerState.FAILED
            self.last_error = str(e)
            self._log_error(f"Background sync failed: {e}")

    def run(self):
        """Main loop for stdio and unix socket MCP server."""
        threading.Thread(target=self._sync_background, daemon=True).start()

        # Unix Socket Listener (Hybrid Dispatch)
        repo_hash = hashlib.sha256(str(self.repo_path.resolve()).encode()).hexdigest()[:12]
        socket_path = Path(f"/tmp/trifecta_f1_{repo_hash}.sock")
        if socket_path.exists(): socket_path.unlink()

        def socket_listener():
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.bind(str(socket_path))
                s.listen(5)
                while True:
                    try:
                        conn, _ = s.accept()
                        with conn:
                            data = b""
                            while True:
                                chunk = conn.recv(4096)
                                if not chunk: break
                                data += chunk
                                if len(data) > 10 * 1024 * 1024:
                                    # 10MB max payload
                                    break
                                if b"\n" in data: break
                            if not data or b"\n" not in data: continue
                            
                            try:
                                req = json.loads(data.decode())
                            except json.JSONDecodeError:
                                continue
                                
                            def socket_respond(rid, res):
                                resp = {"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": json.dumps(res)}]}}
                                try:
                                    conn.sendall(json.dumps(resp).encode() + b"\n")
                                except OSError:
                                    pass # Client disconnected
                            
                            if req.get("method") == "tools/call":
                                self._handle_tool_call(req.get("id"), req.get("params", {}), responder=socket_respond)
                    except Exception: pass

        threading.Thread(target=socket_listener, daemon=True).start()

        # Stdio loop
        try:
            for line in sys.stdin:
                try:
                    req = json.loads(line)
                    method = req.get("method")
                    req_id = req.get("id")
                    if method == "initialize":
                        self._respond_tool(req_id, {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}})
                    elif method == "tools/list":
                        self._respond_tool(req_id, {"tools": self._get_tool_definitions()})
                    elif method == "tools/call":
                        self._handle_tool_call(req_id, req.get("params", {}))
                except: pass
        except KeyboardInterrupt:
            pass

        # Keep alive for unix socket even if stdin closes
        while True:
            time.sleep(1)

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--repo", default=".")
    p.add_argument("--mode", default="auto")
    p.add_argument("--timeout", type=int, default=30)
    args = p.parse_args()
    TrifectaF1Server(args.repo, sync_mode=args.mode, build_timeout=args.timeout).run()

if __name__ == "__main__":
    main()
