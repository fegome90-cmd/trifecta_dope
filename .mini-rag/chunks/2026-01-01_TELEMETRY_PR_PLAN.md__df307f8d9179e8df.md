```python
    # NEW: AST summary
    ast_summary = {
        "ast_parse_count": self.metrics.get("ast_parse_count", 0),
        "ast_cache_hit_count": self.metrics.get("ast_cache_hit_count", 0),
        "ast_cache_hit_rate": round(
            self.metrics.get("ast_cache_hit_count", 0) /
            max(self.metrics.get("ast_parse_count", 1), 1),
            3
        ),
    }

    # NEW: LSP summary
    lsp_summary = {
        "lsp_spawn_count": self.metrics.get("lsp_spawn_count", 0),
        "lsp_ready_count": self.metrics.get("lsp_ready_count", 0),
        "lsp_timeout_count": self.metrics.get("lsp_timeout_count", 0),
        "lsp_fallback_count": self.metrics.get("lsp_fallback_count", 0),
        "lsp_timeout_rate": round(
            self.metrics.get("lsp_timeout_count", 0) /
            max(self.metrics.get("lsp_spawn_count", 1), 1),
            3
        ),
    }

    # NEW: File read summary by mode
    file_read_summary = {
        "skeleton_bytes": self.metrics.get("file_read_skeleton_bytes_total", 0),
        "excerpt_bytes": self.metrics.get("file_read_excerpt_bytes_total", 0),
        "raw_bytes": self.metrics.get("file_read_raw_bytes_total", 0),
        "total_bytes": (
            self.metrics.get("file_read_skeleton_bytes_total", 0) +
            self.metrics.get("file_read_excerpt_bytes_total", 0) +
            self.metrics.get("file_read_raw_bytes_total", 0)
