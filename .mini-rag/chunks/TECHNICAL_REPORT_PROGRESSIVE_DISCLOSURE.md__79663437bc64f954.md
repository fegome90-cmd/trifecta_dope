### 7.1 Modelos de Dominio

**Ubicación**: `src/domain/context_models.py`

```python
class ContextChunk(BaseModel):
    id: str
    doc: str
    title_path: List[str]
    text: str
    token_est: int
    source_path: str

class GetResult(BaseModel):
    chunks: List[ContextChunk]
    total_tokens: int
    stop_reason: str  # "complete", "budget", "max_chunks", "evidence"
    evidence_metadata: dict
```
