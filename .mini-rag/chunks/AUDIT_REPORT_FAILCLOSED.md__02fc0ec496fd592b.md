### C.2) Token efficiency (SCOOP sección 3, métrica 3)

**Propuesta SCOOP**:
```bash
uv run trifecta session query -s . --last 5 --format raw | wc -w
uv run trifecta session query -s . --last 5 --format clean | wc -w
```

**PROBLEMAS**:
1. ❌ `wc -w` cuenta words, NO tokens (diferente para tokenizer real)
2. ❌ No hay tokenizer definido (¿GPT? ¿Claude? ¿LLaMA?)
3. ❌ "30% reducción" es threshold arbitrario sin justificación

**OPCIONES**:

**Opción A** (simple): Cambiar contrato a **bytes** (determinista):
```bash
# Tamaño raw
raw_bytes=$(uv run trifecta session query -s . --last 5 --format raw | wc -c)

# Tamaño clean
clean_bytes=$(uv run trifecta session query -s . --last 5 --format clean | wc -c)

# Reducción
reduction=$((100 - (clean_bytes * 100 / raw_bytes)))
echo "Reducción: ${reduction}%"

# GATE: ≥ 30%
[ $reduction -ge 30 ] && echo "✅ PASS" || echo "❌ FAIL"
```

**Opción B** (preciso): Integrar tokenizer (ej: `tiktoken` para GPT):
```python
import tiktoken

enc = tiktoken.encoding_for_model("gpt-4")
raw_tokens = len(enc.encode(raw_output))
clean_tokens = len(enc.encode(clean_output))
reduction = ((raw_tokens - clean_tokens) / raw_tokens) * 100
```

**BLOCKER #4**: SCOOP debe especificar: ¿bytes o tokens? Si tokens, ¿qué tokenizer?

**RECOMENDACIÓN**: Usar bytes (simple, determinista) con threshold ≥ 30%

---
