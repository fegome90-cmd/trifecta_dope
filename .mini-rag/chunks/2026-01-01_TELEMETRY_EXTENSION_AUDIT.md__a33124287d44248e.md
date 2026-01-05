```python
class LSPClient:
    def __init__(self, telemetry: Telemetry):
        self.telemetry = telemetry
        self.spawn_time_ns = time.perf_counter_ns()

        self.telemetry.event(
            "lsp.spawn",
            {"pyright_binary": PYRIGHT_BIN},
            {"subprocess_pid": self.process.pid},
            0,  # timing_ms will be updated on ready
        )
        self.telemetry.incr("lsp_spawn_count")

    def send_request(self, method: str, params: dict) -> dict:
        start_ns = time.perf_counter_ns()
        try:
            response = self._do_send(method, params)
            elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000

            self.telemetry.event(
                f"lsp.{method.split('/')[-1]}",
                {"method": method, "params_hash": hash(str(params))},
                {"success": True, "response_keys": list(response.keys())},
                int(elapsed_ms),
            )
            return response
        except TimeoutError:
            elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000

            self.telemetry.event(
                "lsp.timeout",
                {"method": method},
                {"timeout_ms": 500},
                int(elapsed_ms),
                fallback_to="tree_sitter"
            )
            self.telemetry.incr("lsp_timeout_count")
            raise
```
