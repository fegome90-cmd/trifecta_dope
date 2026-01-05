self.telemetry.incr("ast_parse_count")

            return skeleton

        except Exception as e:
            elapsed_ns = time.perf_counter_ns() - start_ns
            elapsed_ms = int(elapsed_ns / 1_000_000)

            self.telemetry.event(
                "ast.parse",
                {"file": self._relative_path(file_path)},
                {"status": "error", "error": str(e)},
                elapsed_ms,
            )
            raise

    def _extract_structure(self, tree) -> tuple:
        """Extract functions, classes, imports from AST tree."""
        # Pseudocode: walk tree, identify function_definition / class_definition / import_statement nodes
        # Return (functions, classes, imports) lists
        # ACTUAL IMPLEMENTATION: Use tree-sitter Python query language
        return [], [], []

class LSPClient:
    """JSON-RPC client for Pyright language server."""

    def __init__(self, telemetry: Telemetry, pyright_binary: str = "pyright-langserver"):
        self.telemetry = telemetry
        self.pyright_binary = pyright_binary
        self.process: Optional[subprocess.Popen] = None
        self.initialized = False
        self._message_id = 0

        self.spawn_time_ns = time.perf_counter_ns()

        try:
            self.process = subprocess.Popen(
                [pyright_binary],
                stdin=subprocess.PIPE,
                stdout=subproc
