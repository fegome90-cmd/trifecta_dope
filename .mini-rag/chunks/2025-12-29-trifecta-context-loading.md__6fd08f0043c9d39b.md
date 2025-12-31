#### 5. **Observability** (logs + métricas mínimas)

**De**: observability-agent/metrics  
**Para Trifecta**: Log + métricas básicas

```python
class IngestMetrics:
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.metrics = {
            "chunks_total": 0,
            "chars_total": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "elapsed_ms": 0
        }
    
    def record(self, **kwargs):
        for k, v in kwargs.items():
            if k in self.metrics:
                self.metrics[k] += v
    
    def write_log(self):
        with open(self.log_path, 'a') as f:
            f.write(f"{datetime.now().isoformat()} {json.dumps(self.metrics)}\n")
```

**ROI**: Medio. Ahorra depuración.

---
