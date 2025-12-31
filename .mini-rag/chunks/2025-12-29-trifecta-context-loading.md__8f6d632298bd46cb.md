#### 2. Go-to-Definition + Hover

**Navegación precisa**:
```python
# Agente pregunta por función importada
definition = lsp.definition("build_pack", "cli.py:156")
# Router trae rango exacto

hover = lsp.hover("build_pack", "cli.py:156")
# Docstring + tipos para resumen ultracorto
```
