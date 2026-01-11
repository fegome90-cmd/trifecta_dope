### Detalles:

**1. ContextPack DUPLICADO (SSOT VIOLATION - ALTA):**

```python
# SSOT: src/domain/context_models.py:39-48
class ContextPack(BaseModel):
    schema_version: int = 1
    segment: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    digest: str = ""
    source_files: List[SourceFile] = Field(default_factory=list)
    chunks: List[ContextChunk]
    index: List[ContextIndexEntry]

# DUPLICADO: src/domain/models.py:100-105
@dataclass(frozen=True)
class ContextPack:
    """Complete context pack (schema v1)."""
    schema_version: int
    segment_id: str
    created_at: str
    # ... (diferente estructura!)
```

**Impacto**: Dos definiciones distintas del mismo concepto causan ambigüedad y bugs potenciales.

**2. segment_id DERIVACIÓN (SSOT PARCIAL - MEDIA):**

```python
# SSOT: src/infrastructure/segment_utils.py:31-37
def compute_segment_id(segment_root: Path) -> str:
    path_str = str(segment_root.resolve())
    return hashlib.sha256(path_str.encode("utf-8")).hexdigest()[:8]

# DERIVACIÓN (no duplicación exacta): src/domain/models.py:24-29
@property
def segment_id(self) -> str:
    """Derive normalized segment ID from segment name."""
    from src.domain.naming import normalize_segment_id
    return normalize_segment_id(self.segment)
```
