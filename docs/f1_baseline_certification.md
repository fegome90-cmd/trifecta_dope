# F1 Baseline Certification Report

### 1) Scope Closure
- **F1 queda cerrado como prioridad de optimización del hot path actual**.
- **F1 NO queda cerrado para retrieval semántico / signal fusion**.
- Estado actual: Fallback estructural/documental (AST + PRIME).

### 2) Qué quedó certificado realmente
- **Latencia de Backend (Daemon):** Quedó probado estadísticamente que el Daemon en memoria resuelve consultas en un promedio de **13.22 ms**, mitigando el I/O por carga de contexto (que tomaba ~13.21 ms en frío).
- **Latencia End-to-End Oficial (Fast Client):** El uso del cliente `trifecta-fast.py` entrega una latencia promedio de **~49 ms** y un P95 de **~61 ms**. Este es un baseline operativo aceptable para agentes.
- **Impacto de Inicialización:** El cliente pesado (`uv run trifecta`) toma un promedio de **217.29 ms**, demostrando que ~168 ms corresponden a la inicialización del intérprete Python y la librería Typer, no al procesamiento de Trifecta.
- **Cache en RAM (SSOT):** La política de invalidación por tupla `mtime`/`size` y el volcado con publicación atómica (`os.fsync` y `os.replace`) logran una invalidación consistente y establecen el JSON como un artefacto autoritativo local del hot path F1 / recuperación de contexto.

### 3) Qué no quedó certificado aún
- **Calidad de Retrieval Semántico (Signal Fusion):** La calidad medida corresponde exclusivamente al *fallback* estructural/documental (Hits promedio: 4.0, Fidelidad reportada: {'fallback': 100}).
- **Impacto Multi-Tenant en RAM:** Aunque el cache LRU limita a 5 packs concurrentes por proceso, el OOM footprint real bajo cargas concurrentes multi-repositorio no fue puesto a prueba.

### 4) Cuál es la surface oficial congelada para agentes
**El cliente `scripts/trifecta-fast.py` queda declarado como cliente oficial para agentes y automatización.**
- **Contrato mínimo congelado:** 
  - Resolución de socket determinista (basada en el path del repositorio).
  - Shape de request (JSON-RPC 2.0 estándar de MCP).
  - Shape de response (lista de chunks o explicación estructurada).
  - Errores básicos (manejo explícito de fallback o conexión rechazada).
- **Single Source of Truth:** `src/infrastructure/daemon_client.py` es la referencia obligatoria como única fuente de verdad del contrato de conexión. Esto minimiza el riesgo de drift, centraliza el contrato y queda protegido mediante tests de paridad.

### 5) Cuál es el estado real de F1 hoy
**F1 opera como un motor de contexto en Fallback Mode.**
Resolvió la problemática de latencia en "hot path" sin depender de I/O en disco para lecturas frecuentes. No obstante, **F1 actual no implementa signal fusion semántica real** dado que el cliente LSP se omite deliberadamente en el orquestador (`server.py`), forzando una respuesta basada estrictamente en AST y PRIME.

### 6) Cuál es el estado de WO-0043 en el roadmap
**WO-0043 (SQLite + Daemon) queda redefinido y fuera del critical path actual.**
No está justificado para mejorar la latencia del hot path, dado que JSON + RAM funciona como baseline operativo aceptable. Introducirlo en este flujo presenta riesgos si se duplica la autoridad (JSON vs DB).
Solo se retomará por:
- Graph derivado.
- Vector store.
- Consultas avanzadas (fuera de alcance de búsqueda de keywords/AST).

### 7) Reopen Criteria for LSP/Signal Fusion
El desarrollo de la Signal Fusion semántica se retomará exclusivamente cuando se cumplan las siguientes condiciones:
1. **Calidad y Métrica:** Exista un benchmark de calidad definido y aprobado antes de integrar.
2. **Performance:** Se demuestre que el costo de la consulta semántica entra dentro de un presupuesto de latencia aceptable para el hot path.
3. **Resiliencia:** Exista una estrategia formal de degradación explícita cuando el LSP falle.
4. **Test Suite:** Se disponga de una suite adversarial determinista que cubra explícitamente timeouts del servidor, símbolos ambiguos, caídas del AST y respuestas parciales.

### 8) Next Active Front
- F1 performance queda cerrada.
- El siguiente frente activo es el benchmark de calidad para LSP/signal fusion.
- No debe iniciarse integración LSP sin cumplir los Reopen Criteria.

---
*Este documento queda congelado y solo podrá reabrirse con nueva evidencia empírica, cambio de requisitos o ADR aprobada.*
