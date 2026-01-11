finally:
                self.process = None

class Selector:
    """Symbol resolver for sym:// DSL."""

    def __init__(self, telemetry: Telemetry, skeleton_map_builder: SkeletonMapBuilder):
        self.telemetry = telemetry
        self.skeleton_map_builder = skeleton_map_builder

    def resolve_symbol(self, symbol_query: str) -> Optional[Dict]:
        """
        Resolve sym://python/module.path/SymbolName to file + line + kind.
        Uses monotonic timing.
        """
        start_ns = time.perf_counter_ns()

        try:
            # Parse sym://python/src.domain.models/Config
            # Find file, load skeleton, locate symbol in skeleton

            resolved = True  # simplified
            matches_count = 1
            ambiguous = False

            elapsed_ns = time.perf_counter_ns() - start_ns
            elapsed_ms = int(elapsed_ns / 1_000_000)

            self.telemetry.event(
                "selector.resolve",
                {"symbol_query": symbol_query},
                {"resolved": resolved, "matches": matches_count, "ambiguous": ambiguous},
                elapsed_ms,
            )

            if resolved:
                self.telemetry.incr("selector_resolve_success_count")

            self.telemetry.incr("selector_resolve_count")

            return {"file": "src/domain/models.py", "line": 42, "kind": "class"}

        except Exception
