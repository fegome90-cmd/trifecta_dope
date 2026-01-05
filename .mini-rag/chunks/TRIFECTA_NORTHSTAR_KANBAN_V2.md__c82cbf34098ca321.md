### PCC (Programming Context Calling)
- [x] **Progressive Disclosure (Search/Get)** `#priority:high` `#phase:2`
  - **Trace**: [`src/application/context_service.py:35`](file:///Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/src/application/context_service.py#L35)
  - **Symbols**: `ContextService` (L35), `parse_chunk_id` (L10)
  - **Methods**: `search()`, `get(mode=raw|excerpt|skeleton)`, `_check_evidence()`
  - **Tests**: `tests/unit/test_chunking.py`
  - **Status**: ✅ Evidence-based early-stop implemented

- [x] **Macro Load (PCC + Fallback)** `#priority:high` `#phase:2`
  - **Trace**: [`src/application/use_cases.py:488`](file:///Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/src/application/use_cases.py#L488)
  - **Symbols**: `MacroLoadUseCase` (L488)
  - **Tests**: Acceptance tests passing
  - **Status**: ✅ Plan A (PCC) + Plan B (Fallback) verified
