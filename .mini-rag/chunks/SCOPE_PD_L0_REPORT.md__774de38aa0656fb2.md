### Snippets Relevantes

**src/application/context_service.py:100-117**
```python
        for chunk_id in ids:
            chunk = chunk_map.get(chunk_id)
            if not chunk: continue

            # Progressive Disclosure logic
            text = chunk.text
            if mode == "excerpt":
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                excerpt_lines = lines[:25]
                text = "\n".join(excerpt_lines)
                if len(lines) > 25:
                    text += "\n\n... [Contenido truncado, usa mode='raw' para ver todo]"
            elif mode == "skeleton":
                text = self._skeletonize(text)
            elif mode == "raw":
                token_est = len(text) // 4
                if total_tokens + token_est > budget:
                    # Fallback to excerpt with note
                    lines = [line.strip() for line in text.split("\n") if line.strip()]
                    text = "\n".join(lines[:20]) + "\n\n> [!NOTE]\n> Chunk truncado por presupuesto..."
```

---
