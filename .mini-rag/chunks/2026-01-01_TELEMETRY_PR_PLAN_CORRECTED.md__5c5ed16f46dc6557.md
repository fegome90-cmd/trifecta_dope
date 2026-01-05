ytes_total", 0),
        "excerpt_bytes": self.metrics.get("file_read_excerpt_bytes_total", 0),
        "raw_bytes": self.metrics.get("file_read_raw_bytes_total", 0),
        "total_bytes": (
            self.metrics.get("file_read_skeleton_bytes_total", 0) +
            self.metrics.get("file_read_excerpt_bytes_total", 0) +
            self.metrics.get("file_read_raw_bytes_total", 0)
        ),
    }

    # (Keep existing latency_summary and tokens_summary code)

    run_summary = {
        "run_id": self.run_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "metrics_delta": self.metrics,
        "latencies": latency_summary,
        "tokens": tokens_summary,
        "ast": ast_summary,              # NEW
        "lsp": lsp_summary,              # NEW
        "file_read": file_read_summary,  # NEW
        "telemetry_drops": {             # NEW: track lossy fcntl drops
            "lock_skipped": self.metrics.get("telemetry_lock_skipped", 0),
            "drop_rate": round(
                self.metrics.get("telemetry_lock_skipped", 0) /
                max(sum(self.metrics.values()), 1),
                4
            ),
        },
        "top_warnings": self.warnings[:5],
        "pack_state": {
            "pack_sha": self.pack_sha,
            "pack_mtime": self.pack_mtime,
            **(
                {}
                if self.stale_detected is None
