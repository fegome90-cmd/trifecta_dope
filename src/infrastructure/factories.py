import os
from pathlib import Path
from typing import TYPE_CHECKING

from src.domain.ast_cache import AstCache, InMemoryLRUCache, SQLiteCache

if TYPE_CHECKING:
    from src.infrastructure.telemetry import Telemetry

CACHE_DIR_NAME = ".trifecta"


def get_ast_cache(
    persist: bool = False,
    segment_id: str = ".",
    telemetry: "Telemetry | None" = None,
    max_entries: int = 10000,
    max_bytes: int = 100 * 1024 * 1024,
) -> AstCache:
    """
    Factory centralizada para AstCache.

    Reglas de decisión:
    1. Si 'persist' es True explícitamente -> SQLiteCache
    2. Si env var TRIFECTA_AST_PERSIST=1 -> SQLiteCache
    3. Default -> InMemoryLRUCache

    Args:
        persist: Override manual para forzar persistencia
        segment_id: ID del segmento (usado para nombrar el archivo DB)
        telemetry: Optional telemetry instance for event emission
        max_entries: Límite de entradas LRU
        max_bytes: Límite de bytes

    Returns:
        Instancia de AstCache (SQLite o InMemory), potentially wrapped with telemetry
    """
    should_persist = persist or os.environ.get("TRIFECTA_AST_PERSIST", "0") == "1"

    if should_persist:
        # P3 Path Compliance: Use cwd/.trifecta/cache by default for now
        # Future: Resolve from segment_root if passed explicitly
        cache_dir = Path.cwd() / CACHE_DIR_NAME / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Deterministic filename based on segment_id
        # sanitize segment_id to be safe for filenames
        safe_id = segment_id.replace("/", "_").replace("\\", "_").replace(":", "_")
        if safe_id == ".":
            # If segment_id is dot (default), try to map to safe path of cwd
            safe_id = str(Path.cwd()).replace("/", "_").replace("\\", "_").replace(":", "_")

        db_path = cache_dir / f"ast_cache_{safe_id}.db"

        # Wire: Create persistent cache
        cache: AstCache = SQLiteCache(db_path=db_path, max_entries=max_entries, max_bytes=max_bytes)

        # Wrap with file lock for deterministic timeout + telemetry
        from src.infrastructure.file_locked_cache import FileLockedAstCache

        lock_path = db_path.with_suffix(".lock")
        cache = FileLockedAstCache(inner=cache, lock_path=lock_path, telemetry=telemetry)
    else:
        # Wire: Return ephemeral cache
        cache = InMemoryLRUCache(max_entries=max_entries, max_bytes=max_bytes)

    # Wrap with telemetry if available
    if telemetry is not None:
        from src.infrastructure.telemetry_cache import TelemetryAstCache

        return TelemetryAstCache(cache, telemetry, segment_id)

    return cache
