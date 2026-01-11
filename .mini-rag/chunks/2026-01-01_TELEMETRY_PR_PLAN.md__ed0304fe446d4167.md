": str(file_path.name), "line": line, "col": col},
                    {"resolved": True, "target_file": target_file, "target_line": target_line},
                    elapsed_ms,
                )

            self.telemetry.incr("lsp_definition_count")
            return response

        except TimeoutError:
            elapsed_ns = time.perf_counter_ns() - start_ns
            elapsed_ms = int(elapsed_ns / 1_000_000)

            self.telemetry.event(
                "lsp.timeout",
                {"method": "definition"},
                {"timeout_ms": 500},
                elapsed_ms,
                fallback_to="tree_sitter"
            )

            self.telemetry.incr("lsp_timeout_count")
            self.telemetry.incr("lsp_fallback_count")

            raise

    def _send_request(self, method: str, params: dict, timeout_ms: int = 500) -> Optional[dict]:
        """Send JSON-RPC request, wait for response."""
        # Pseudocode: assemble JSON-RPC message, send, wait for response, parse
        # ACTUAL: Use python-jsonrpc2 or similar
        pass

    def shutdown(self) -> None:
        """Kill LSP process."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
            finally:
                self.process = None

class Selector:
