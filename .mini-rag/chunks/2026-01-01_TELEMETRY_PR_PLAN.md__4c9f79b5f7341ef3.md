", 0) +
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
        "top_warnings": self.warnings[:5],
        "pack_state": {
            "pack_sha": self.pack_sha,
            "pack_mtime": self.pack_mtime,
            **(
                {}
                if self.stale_detected is None
                else {"stale_detected": self.stale_detected}
            ),
        },
    }
```
