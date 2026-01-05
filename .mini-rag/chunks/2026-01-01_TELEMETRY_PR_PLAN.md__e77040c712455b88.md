stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            self.telemetry.event(
                "lsp.spawn",
                {"pyright_binary": pyright_binary},
                {"subprocess_pid": self.process.pid, "status": "ok"},
                0,
            )

            self.telemetry.incr("lsp_spawn_count")

        except Exception as e:
            self.telemetry.event(
                "lsp.spawn",
                {"pyright_binary": pyright_binary},
                {"status": "error", "error": str(e)},
                0,
            )
            raise

    def initialize(self, workspace_path: Path) -> None:
        """Send LSP initialize request."""
        start_ns = time.perf_counter_ns()

        try:
            # Construct and send initialize JSON-RPC request
            # (Pseudocode; actual implementation: send JSON-RPC message)

            elapsed_ns = time.perf_counter_ns() - start_ns
            elapsed_ms = int(elapsed_ns / 1_000_000)

            self.telemetry.event(
                "lsp.initialize",
                {"workspace": str(workspace_path)},
                {"status": "ok", "initialized": True},
                elapsed_ms,
            )

            self.initialized = True

        except Exception as e:
            elapsed_ns = t
