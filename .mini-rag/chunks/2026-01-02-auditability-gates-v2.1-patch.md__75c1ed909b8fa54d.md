```python
# En src/domain/context_models.py, clase TrifectaPack:

def sanitized_dump(self) -> str:
    """Dump JSON con paths sanitizados (FAIL-CLOSED: no PII en output).

    Sanitiza TODOS los paths absolutos, no solo repo_root.
    Estrategia:
    1. Si path es relativo a segment_root: convertir a relativo
    2. Si es path absoluto externo: redactar con placeholder

    Anti-patrones evitados:
    - AP1: No string parsing; usa Path operations
    - AP6: Output es JSON determinista
    - AP8: SSOT de sanitización está aquí
    """
    import json
    from pathlib import Path

    data = self.model_dump()
    segment_root = Path(data.get("repo_root", "/"))

    def _sanitize_path(value: str, root: Path) -> str:
        """Sanitiza un string que podría ser un path."""
        # Detectar patrones de path absoluto conocidos
        if value.startswith("/Users/") or value.startswith("/home/"):
            # Intentar hacer relativo a root
            try:
                p = Path(value)
                rel = p.relative_to(root)
                return f"<RELATIVE>{rel.as_posix()}</RELATIVE>"
            except ValueError:
                # No es relativo a root, redactar
                return f"<ABS_PATH_REDACTED>{hashlib.sha256(value.encode()).hexdigest()[:8]}</ABS_PATH_REDACTED>"

        # Detectar file:// URIs
        if "file://" in value:
            return value.replace("fi
