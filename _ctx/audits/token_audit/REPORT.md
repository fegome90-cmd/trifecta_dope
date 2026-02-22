A) Definición del experimento
- Experimento: 'required artifacts en cierre de WO'.
- Interacción definida: tools + síntesis final.
- Precio congelado GPT-5.2: INPUT=1.75, OUTPUT=14.00, CACHED_INPUT=0.175 (cached no aplicado).
- Método de tokens: tiktoken `encoding_for_model("gpt-4.1")`, UTF-8, JSON canónico para args/result.

B) Datos medidos
| Item | Tokens In | Tokens Out | Fuente | Tipo |
|---|---:|---:|---|---|
| ctx.search (run_1771428828) | 100 | 132 | /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/_ctx/telemetry/events.jsonl | MEDIDO |
| ctx.get (run_1771428838) | 43 | 255 | /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/_ctx/telemetry/events.jsonl | MEDIDO |
| A tools totals | 143 | 387 | /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/_ctx/telemetry/events.jsonl | MEDIDO |
| Synthesis OUT | 0 | 2157 | /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/_ctx/audits/token_audit/synthesis_final.txt | MEDIDO |
| Synthesis IN | MISSING | 0 | /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/_ctx/audits/token_audit/synthesis_prompt.txt | MISSING |

C) Escenario A tools-only (100% medido)
- TOTAL_IN_A_TOOLS = 143
- TOTAL_OUT_A_TOOLS = 387
- TOTAL_A_TOOLS_ONLY = 530
- COST_IN_A_TOOLS = 0.00025025
- COST_OUT_A_TOOLS = 0.005418
- COST_TOTAL_A_TOOLS = 0.00566825

D) Baselines B1/B2/B3 (input dumping medido)
- B1: TOKENS_IN=3653 COST_IN=0.00639275 (MEDIDO, dedupe)
- B2: TOKENS_IN=14485 COST_IN=0.02534875 (MEDIDO, dedupe)
- B3: TOKENS_IN=27173 COST_IN=0.04755275 (MEDIDO, dedupe)

E) Resultados tools-only
- Fórmula % ahorro input: (TOKENS_IN_B - TOKENS_IN_A_TOOLS) / TOKENS_IN_B * 100
- vs_B1: Δtokens_in=3510 Δcost_in=0.00614250 ahorro_pct_in=96.08540925266903914590747331
- vs_B2: Δtokens_in=14342 Δcost_in=0.02509850 ahorro_pct_in=99.01277183293061788056610287
- vs_B3: Δtokens_in=27030 Δcost_in=0.04730250 ahorro_pct_in=99.47374231774187612703786847

F) Task-complete
- status: blocked
- missing: SYNTH_IN_TOKENS, B1_SYNTH_PROMPT_TOKENS, B1_SYNTH_OUT_TOKENS, B2_SYNTH_PROMPT_TOKENS, B2_SYNTH_OUT_TOKENS, B3_SYNTH_PROMPT_TOKENS, B3_SYNTH_OUT_TOKENS
- cannot compute exact %/cost task-complete con datos actuales.

G) Limitaciones
- tools-only y synthesis final OUT están medidos; synthesis IN de la interacción original no está medido de forma trazable.
- B1/B2/B3 no tienen síntesis manual persistida (prompt+out) por escenario.

H) Próxima instrumentación mínima
- En cada respuesta final, persistir `interaction_id`, `synthesis_prompt_tokens`, `synthesis_out_tokens` en telemetry.
- Crear artefactos por baseline: `b*_synthesis_prompt.txt` y `b*_synthesis_out.txt`.
- Repro command: `python3 scripts/audit_tokens.py`.
