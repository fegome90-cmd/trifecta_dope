# Ola 2 + E2 — aliases mínimos para `skill-hub`

## Scope ejecutado
Se ejecutó exactamente este scope y nada más:
1. aplicar solo aliases mínimos en `aliases.yaml`
2. regenerar superficie por flujo normal
3. congelar nuevo freeze
4. correr E2 con el mismo harness validado
5. comparar contra Fase 6 y E1

Restricciones respetadas:
- no se tocó Trifecta
- no se tocó wrapper
- no se tocó harness/parser
- no se tocó `SKILL.md`
- no se tocó corpus adicional
- no se tocó metadocs
- no se modificó benchmark fuera de lo ya reconciliado

## 1. Aliases aplicados
Archivo modificado:
- `~/.trifecta/segments/skills-hub/_ctx/aliases.yaml`

Aliases agregados:

```yaml
  # Ola 2 - planning / coordination / agents
  agenticos:
    - tmux-plan-auditor
    - workorder-execution-base
    - strategic-compact
  planificar:
    - tmux-plan-auditor
    - workorder-execution-base
  coordinate:
    - tmux-plan-auditor
    - workorder-execution-base
    - strategic-compact

  # Ola 2 - debugging / testing
  flaky:
    - debug-helper
    - python-testing
    - superpowers-systematic-debugging

  # Ola 2 - review / PR comments
  comentarios:
    - learned-pr-feedback-resolution
    - branch-review-api
```

### Justificación mínima
- `agenticos` → puente directo para `q01`
- `planificar` → observación secundaria para `q02`
- `coordinate` → observación secundaria para `q12`
- `flaky` → puente directo para `q05`
- `comentarios` → puente directo para `q09`

No se agregaron aliases genéricos como `workflow`, `review`, `pr`, `agents`, `debug`, `testing` para evitar ambigüedad y degradación de controles.

## 2. Regeneración de superficie
Flujo normal ejecutado:
- `uv run trifecta ctx build --segment ~/.trifecta/segments/skills-hub`
- `uv run trifecta ctx validate --segment ~/.trifecta/segments/skills-hub`

Resultado:
- validación pass
- warnings de mtime sin cambio de hash en metadocs ya degradados

## 3. Freeze nuevo
Run dir:
- `eval/results/skill_hub_phase67_e2/20260309T192044Z`

Freeze efectivo:
- `dataset_version`: `post-ola1-reconciled`
- `alias_patch`: `ola2-minimal-aliases-v1`
- `dataset_sha256`: `6cb747d8e11220895414cdde8a4ace9979214970c1756d27d58b740138185bbc`
- `corpus_subset_sha256`: `1454245da4d49b33912193b4d0b8b0a2333716d7ea57b4a3eaac2321ec834465`
- `manifest_sha256`: `5c853b2492a57f2d6b417218bfbf637d35b049f75529afd331ea9aa5a2058f23`
- `context_pack_sha256`: `3b48f0d5f8d5518f679aec68e72af0023e81eaf5188c78e0a29f6748fad183af`
- `aliases_sha256`: `baca98da4ef7de4e662409ff9c611b1bd920b7d7727ff5ca2f28663d218322c0`
- `wrapper_sha256`: `fa78432753b0811b8e6e222167ad67ca58ca6775f321edde5fbc37d94e6f3a7b`
- `parser_sha256`: `d1692435ca1f1e2fec407893a4b512efccb3216a70fb33e3fa609a8e6e77045f`

## 4. Resultados E2
Criterio principal de E2:
- foco: `q01`, `q05`, `q09`
- controles: `q07`, `q10`
- observación secundaria: `q02`, `q12`

### q01
- Phase 6 B: `top3_contains_good_candidate=false`
- E2 B: `top3_contains_good_candidate=false`
- E2 B top3:
  - `dispatching-parallel-agents`
  - `prime_skills-hub`
  - `agent_skills-hub`
- severe false positive nuevo: no

Lectura:
- no mejora
- sigue dominado por naming visible (`dispatching-parallel-agents`) y metadata del segmento
- el alias no alcanzó para forzar entrada de `tmux-plan-auditor` / `workorder-execution-base` / `strategic-compact` en top3 B

### q05
- Phase 6 B: `top3_contains_good_candidate=false`
- E2 B: `top3_contains_good_candidate=true`
- E2 B top3:
  - `plugin-metodo-tdd-first-python`
  - `superpowers-systematic-debugging`
  - `plugin-metodo-fp-python-backend`
- severe false positive nuevo: no

Lectura:
- mejora real
- el alias `flaky` fue suficiente para meter un candidato adyacente válido (`superpowers-systematic-debugging`) dentro de top3
- además desaparece el severe false positive en B para este caso

### q09
- Phase 6 B: `top3_contains_good_candidate=false`
- E2 B: `top3_contains_good_candidate=false`
- E2 B top3:
  - `branch-review`
  - `security-review`
  - `examen-requesting-code-review`
- severe false positive nuevo: no

Lectura:
- no mejora
- el alias `comentarios` no logró subir `learned-pr-feedback-resolution` ni `branch-review-api` a top3
- la superficie sigue dominada por nombres visibles genéricos de review

## 5. Controles
### q07
- Phase 6 B: `true`
- E2 B: `true`
- degradación: no
- severe false positive nuevo: no

### q10
- Phase 6 B: `true`
- E2 B: `true`
- degradación: no
- severe false positive nuevo: no

## 6. Observación secundaria
### q02
- E1 B: `false`
- E2 B: `false`
- sin mejora adicional

### q12
- E1 B: `false`
- E2 B: `false`
- sin mejora adicional

Estas queries no bloquearon el veredicto de E2, pero confirman que el patch de aliases no resuelve el residual de planificación/coordinación.

## 7. Comparación contra Fase 6 y E1
### Contra Fase 6
| query | Phase 6 B | E2 B | cambio |
|---|---:|---:|---|
| `q01` | false | false | no mejora |
| `q05` | false | true | mejora |
| `q09` | false | false | no mejora |
| `q07` | true | true | no degrada |
| `q10` | true | true | no degrada |
| `q02` | false | false | sin cambio |
| `q12` | false | false | sin cambio |

### Contra E1
Disponible para `q07`, `q10`, `q02`, `q12`:
- `q07`: sin cambio
- `q10`: sin cambio
- `q02`: sin cambio
- `q12`: sin cambio

## 8. Veredicto E2
Criterio de éxito pedido:
- `q01`, `q05`, `q09` deben mejorar `top3_contains_good_candidate`
- `q07` y `q10` no deben degradarse
- no deben aparecer severe false positives nuevos
- `q02` y `q12` observación secundaria solamente

Resultado:
- `q01`: fail
- `q05`: pass
- `q09`: fail
- `q07`: pass
- `q10`: pass
- severe false positives nuevos: no

Veredicto E2:
- **fail**

## 9. Lectura residual del fallo
Como E2 falla después de un patch mínimo de aliases, el residual ya no parece principalmente de aliases.

Diagnóstico residual más probable:
- `q01`: **naming visible + metadata**
  - domina `dispatching-parallel-agents`
  - siguen entrando metadocs administrativos en B
- `q09`: **naming visible + contenido buscable / metadata visible**
  - dominan `branch-review`, `security-review`, `requesting-code-review`
  - no suben los skills objetivo aunque exista alias puente
- `q12`: sigue apuntando a **naming visible / metadata** más que a falta de alias

Conclusión residual:
- no parece un problema de caso de uso mal planteado
- no parece un problema de Trifecta
- después de Ola 2, el residual apunta sobre todo a:
  - **naming visible**
  - **metadata visible**
  - y en menor medida **contenido buscable**

No avancé a tocar `SKILL.md` ni a más limpieza del corpus.

## Evidencia
- patch aplicado: `~/.trifecta/segments/skills-hub/_ctx/aliases.yaml`
- freeze: `eval/results/skill_hub_phase67_e2/20260309T192044Z/freeze.json`
- preflight: `eval/results/skill_hub_phase67_e2/20260309T192044Z/preflight.json`
- rows: `eval/results/skill_hub_phase67_e2/20260309T192044Z/rows.jsonl`
- summary: `eval/results/skill_hub_phase67_e2/20260309T192044Z/summary.json`
- comparison: `eval/results/skill_hub_phase67_e2/20260309T192044Z/comparison.json`
- verdict: `eval/results/skill_hub_phase67_e2/20260309T192044Z/verdict.json`
