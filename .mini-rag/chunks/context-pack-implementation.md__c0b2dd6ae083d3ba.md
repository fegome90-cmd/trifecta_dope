### Ejemplo

```python
# Chunk 1
id1 = generate_chunk_id("skill", ["Core Rules"], "Test content")
# → "skill:a1b2c3d4e5"

# Mismo contenido, mismo ID
id2 = generate_chunk_id("skill", ["Core Rules"], "Test content")
# → "skill:a1b2c3d4e5"

# Contenido diferente, ID diferente
id3 = generate_chunk_id("skill", ["Core Rules"], "Different content")
# → "skill:f6e7d8c9b0"

# Distinto documento, IDs independientes
id4 = generate_chunk_id("agent", ["Core Rules"], "Test content")
# → "agent:a1b2c3d4e5" (mismo hash, distinto doc)
```

---
