### T3: Symbol Selector + Progressive Disclosure Integration (4 días)

**Deliverables:**
1. `src/application/context_service.py`: `search_by_symbol()` method
2. `src/application/search_get_usecases.py`: SymbolSearchUseCase wrapper
3. `src/infrastructure/cli.py`: New CLI command `ctx search-symbol`
4. Integration tests: 6 tests
5. Telemetry: skeleton_cache_hit_rate, symbol_resolve_success_rate, bytes_read_per_task

**Definition of Done:**
- [ ] Symbol resolver (sym:// DSL) implemented
- [ ] `search_by_symbol(symbol_name, kind=None)` finds + resolves symbols
- [ ] Disclosure level inference (exact → skeleton, partial → excerpt, etc.)
- [ ] CLI `ctx search-symbol --name "ContextService" --kind "class"`works
- [ ] No breaking changes to existing `ctx search` / `ctx get`
- [ ] 6 integration tests with >75% coverage
- [ ] Telemetry events logged correctly
- [ ] bytes_read_per_task metric tracked (efficiency indicator)

**Tests (Specific):**
```
test_symbol_search_exact_match_1_result
test_symbol_search_partial_match_3_results
test_symbol_search_ambiguous_5_plus_results
test_symbol_disclosure_exact_returns_skeleton
test_symbol_disclosure_partial_returns_excerpt
test_cli_search_symbol_command_integration
```
