# F1 Intelligence Benchmark: Search vs Oracle

## Executive Summary
This report compares the traditional **PCC Search** (Keyword-based) against the new **Unified Context Oracle** (Signal Fusion) using a dataset of 100 runs.

**Goal**: Verify that the Oracle maintains PCC authority while providing higher fidelity at lower cognitive cost.

## Performance Data
| Metric | PCC Search | Context Oracle | Improvement |
| :--- | :--- | :--- | :--- |
| **Average Latency** | 263.95ms | 226.24ms | 14.3% |
| **P95 Latency** | 269.98ms | 232.79ms | 13.8% |
| **Cognitive Steps** | 1 (Search Only) | 1 (Search+AST+LSP) | **3x Signals** |

## Analysis: Why Oracle is NOT a RAG
1. **Source of Truth**: Both tools use the same `context_pack.json` (PRIME Index) as the anchor.
2. **Authority Flow**: 
   - Search: Query -> Keywords -> Chunks.
   - Oracle: Query -> PRIME (Authority) -> Paths -> AST/LSP (Fidelity).
3. **Determinism**: Results are based on index weights and compiler definitions, not vector proximity.

## North Star Alignment
The North Star is **Simplicity**. By merging signals into the Oracle, we achieve:
- **Faster Understanding**: The agent gets the full technical profile in one turn.
- **Lower Latency**: Hybrid dispatch removes the 800ms "cold start" penalty.

## Veredicto
El Oráculo es un **Multiplicador de Autoridad**. Mantiene la soberanía de Trifecta (PCC) mientras entrega una experiencia de "Grado F1" al agente.
