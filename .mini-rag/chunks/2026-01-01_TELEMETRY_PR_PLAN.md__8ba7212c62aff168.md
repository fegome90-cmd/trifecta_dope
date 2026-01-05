in/models.py", "line": 42, "kind": "class"}

        except Exception as e:
            elapsed_ns = time.perf_counter_ns() - start_ns
            elapsed_ms = int(elapsed_ns / 1_000_000)

            self.telemetry.event(
                "selector.resolve",
                {"symbol_query": symbol_query},
                {"resolved": False, "error": str(e)},
                elapsed_ms,
            )

            raise
```
