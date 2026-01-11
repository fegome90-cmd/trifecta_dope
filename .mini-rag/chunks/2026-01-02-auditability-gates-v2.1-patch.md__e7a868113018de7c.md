Is
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
    return json.dumps(data, indent=2)
```
