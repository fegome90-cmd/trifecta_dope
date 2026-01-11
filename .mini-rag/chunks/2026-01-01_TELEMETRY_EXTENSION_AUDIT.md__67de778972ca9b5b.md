#### C.1.2 AST Layer (NEW Module)

**File:** `src/infrastructure/ast_lsp.py` (NEW)

**Hooks in SkeletonMapBuilder:**
```python
class SkeletonMapBuilder:
    def __init__(self, telemetry: Telemetry):
        self.telemetry = telemetry

    def parse_python(self, code: str, file_path: Path) -> SkeletonMap:
        start_ns = time.perf_counter_ns()
        skeleton = self._do_parse(code)
        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000

        self.telemetry.event(
            "ast.parse",
            {"file": str(file_path.relative_to(...))},
            {"functions": len(skeleton.functions), "classes": len(skeleton.classes)},
            int(elapsed_ms),
            skeleton_bytes=len(json.dumps(skeleton)),
            reduction_ratio=len(json.dumps(skeleton)) / len(code)
        )
        self.telemetry.incr("ast_parse_count")
        return skeleton
```
