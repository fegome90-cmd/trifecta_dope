ntar hacer relativo a root
            try:
                p = Path(value)
                rel = p.relative_to(root)
                return f"<RELATIVE>{rel.as_posix()}</RELATIVE>"
            except (ValueError, OSError):
                # No es relativo a root, redactar
                return f"<ABS_PATH_REDACTED>{hashlib.sha256(value.encode()).hexdigest()[:8]}</ABS_PATH_REDACTED>"

        # Detectar file:// URIs
        if "file://" in value:
            return value.replace("file://", "<FILE_URI_SANITIZED>")

        return value

    def _sanitize(obj):
        """Sanitiza recursivamente todas las strings."""
        if isinstance(obj, str):
            return _sanitize_path(obj, segment_root)
        elif isinstance(obj, dict):
            return {k: _sanitize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_sanitize(item) for item in obj]
        return obj

    data = _sanitize(data)

    # v2.2 FIX: json.dumps ahora siempre recibe datos serializables
    return json.dumps(data, indent=2)
```
