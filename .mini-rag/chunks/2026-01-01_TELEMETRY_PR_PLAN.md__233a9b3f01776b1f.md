ized = True

        except Exception as e:
            elapsed_ns = time.perf_counter_ns() - start_ns
            elapsed_ms = int(elapsed_ns / 1_000_000)

            self.telemetry.event(
                "lsp.initialize",
                {"workspace": str(workspace_path)},
                {"status": "error", "error": str(e)},
                elapsed_ms,
            )
            raise

    def definition(self, file_path: Path, line: int, col: int) -> Optional[Dict]:
        """Request textDocument/definition."""
        start_ns = time.perf_counter_ns()

        try:
            # Send textDocument/definition request, wait for response (timeout 500ms)
            response = self._send_request("textDocument/definition", {
                "textDocument": {"uri": file_path.as_uri()},
                "position": {"line": line, "character": col}
            }, timeout_ms=500)

            elapsed_ns = time.perf_counter_ns() - start_ns
            elapsed_ms = int(elapsed_ns / 1_000_000)

            if response:
                # Extract file + line from response
                target_file = response.get("uri", "unknown")
                target_line = response.get("range", {}).get("start", {}).get("line", 0)

                self.telemetry.event(
                    "lsp.definition",
                    {"file": str(file_path.name), "line": line, "col": col},
