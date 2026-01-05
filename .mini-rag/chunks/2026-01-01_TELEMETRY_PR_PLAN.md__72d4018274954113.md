```python
"""AST + LSP integration with instrumentation."""

import json
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from src.infrastructure.telemetry import Telemetry

@dataclass
class SkeletonMap:
    """Parsed Python structure (functions, classes, imports)."""
    functions: List[Dict[str, Any]]
    classes: List[Dict[str, Any]]
    imports: List[str]
    file_path: Path

class SkeletonMapBuilder:
    """Build skeleton maps using Tree-sitter Python parser."""

    def __init__(self, telemetry: Telemetry, segment_root: Path):
        self.telemetry = telemetry
        self.segment_root = segment_root
        self._skeleton_cache: Dict[str, SkeletonMap] = {}
        self._file_sha_cache: Dict[Path, str] = {}

    def _relative_path(self, path: Path) -> str:
        """Convert to relative path for telemetry (redaction)."""
        try:
            return str(path.relative_to(self.segment_root))
        except ValueError:
            return str(path.name)

    def parse_python(self, code: str, file_path: Path) -> SkeletonMap:
        """
        Parse Python code, extract structure (functions/classes only).
        Uses monotonic clock for timing.
        """
        start_ns = time.perf_counter_ns()

        try:
            # Import tree-sitter on first use
            from tree_sitter im
