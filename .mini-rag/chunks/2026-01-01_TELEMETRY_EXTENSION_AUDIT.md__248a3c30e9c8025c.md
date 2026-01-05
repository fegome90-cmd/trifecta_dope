```python
# After line 242 (latency_summary built)
ast_summary = {
    "ast_parse_count": self.metrics.get("ast_parse_count", 0),
    "ast_cache_hit_rate": (
        self.metrics.get("ast_cache_hit_count", 0) /
        self.metrics.get("ast_parse_count", 1)
    ),
}

lsp_summary = {
    "lsp_spawn_count": self.metrics.get("lsp_spawn_count", 0),
    "lsp_ready_count": self.metrics.get("lsp_ready_count", 0),
    "lsp_timeout_count": self.metrics.get("lsp_timeout_count", 0),
    "lsp_timeout_rate": (
        self.metrics.get("lsp_timeout_count", 0) /
        max(self.metrics.get("lsp_spawn_count", 1), 1)
    ),
    "lsp_fallback_count": self.metrics.get("lsp_fallback_count", 0),
}

file_read_summary = {
    "skeleton_bytes": self.metrics.get("file_read_skeleton_bytes_total", 0),
    "excerpt_bytes": self.metrics.get("file_read_excerpt_bytes_total", 0),
    "raw_bytes": self.metrics.get("file_read_raw_bytes_total", 0),
    "total_bytes": (
        self.metrics.get("file_read_skeleton_bytes_total", 0) +
        self.metrics.get("file_read_excerpt_bytes_total", 0) +
        self.metrics.get("file_read_raw_bytes_total", 0)
    ),
}

run_summary = {
    "run_id": self.run_id,
    "ts": datetime.now(timezone.utc).isoformat(),
    "metrics_delta": self.metrics,
    "latencies": latency_summary,
    "tokens": tokens_summary,
    "ast": ast_summary,          # NEW
    "lsp": lsp_summary,
