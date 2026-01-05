Dataset:
   - Tipo: Real
   - Tamaño: All session entries (≥100 mínimo)
   - Worst-case: Entry con campos opcionales vacíos
   - Representativo: SÍ
   Umbral: PASS si ≥ 99%
   Justificación: Schema corruption rompe queries

3. **Métrica**: Token efficiency (vs status quo)
   Definición: Reducción de tokens por entry al filtrar campos telemetry
   Fórmula: `(tokens_raw - tokens_clean) / tokens_raw * 100`
   Comando:
   ```bash
   # Comparar output raw vs clean
   uv run trifecta session query -s . --last 5 --format raw | wc -w
   uv run trifecta session query -s . --last 5 --format clean | wc -w
   ```
   Dataset:
   - Tipo: Real
   - Tamaño: 100 session entries
   - Worst-case: Entry con todos los campos opcionales populated
   - Representativo: SÍ
   Umbral: PASS si ≥ 30% reducción
   Justificación: North Star exige "pocos tokens"

**FRACASO**:

1. **Métrica**: Backward compatibility violation rate
   Definición: % de comandos existentes que rompen después del cambio
   Fórmula: `(broken_commands / total_critical_commands) * 100`
   Comando:
   ```bash
   # Run existing integration tests
   pytest tests/integration/test_session_*.py -v | grep FAILED | wc -l
   ```
