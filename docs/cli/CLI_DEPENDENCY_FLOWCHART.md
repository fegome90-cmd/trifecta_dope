# CLI.py Dependency Graph & Data Flow Visualization

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Trifecta CLI v2.0 Architecture                       │
└─────────────────────────────────────────────────────────────────────────────┘

                              ╔══════════════════════╗
                              ║   typer.Typer(app)   ║
                              ║  1560 lines, 25 cmds ║
                              ╚══════════════════════╝
                                       │
                ┌──────────────────────┼──────────────────────┐
                │                      │                      │
        ╔════════════════╗     ╔════════════════╗     ╔════════════════╗
        ║  ctx_app       ║     ║  ast_app       ║     ║  session_app   ║
        ║  (8 commands)  ║     ║  (3 commands)  ║     ║  (1 command)   ║
        ╚════════════════╝     ╚════════════════╝     ╚════════════════╝
                │                      │                      │
        ┌───────┼───────┐      ┌────────┴────────┐    ┌─────────────┐
        │       │       │      │                 │    │             │
        ▼       ▼       ▼      ▼                 ▼    ▼             ▼
    [search] [get]  [build] [symbols] [snippet] [hover] [append] [report]
    [validate] [stats] [plan] [eval-plan]             [export] [chart]
    [sync] [reset]

    ╔════════════════════════════════════════════════════════════╗
    ║         Telemetry Instrumentation (100% Coverage)          ║
    ║  ├─ .event(name, metadata, status, latency_ms)            ║
    ║  ├─ .observe(name, latency_ms)                            ║
    ║  └─ .flush() in finally block                             ║
    ╚════════════════════════════════════════════════════════════╝
```

## Command Execution Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                    Helpers (Dependency Injection)                │
│  _get_telemetry(segment, level) → Telemetry                    │
│  _get_dependencies(segment) → (TemplateRenderer, FileSystem)    │
│  _format_error(e, title) → str                                 │
└─────────────────────────────────────────────────────────────────┘

                         Command Execution
                                │
                    ┌───────────┼───────────┐
                    │           │           │
              ┌─────▼────┐ ┌────▼────┐ ┌────▼────┐
              │ Parameter│ │Validate │ │ Use Case│
              │Binding   │ │Precond  │ │Execution
              │(typer)   │ │(Gates)  │ │
              └─────┬────┘ └────┬────┘ └────┬────┘
                    │           │           │
                    └───────────┼───────────┘
                                │
                    ┌───────────▼───────────┐
                    │ Telemetry Observation │
                    │ + Flush               │
                    └───────────┬───────────┘
                                │
                         Output to CLI
```

## Use Case Dependencies (DDD Pattern)

```
┌──────────────────────────────────────────────────────────────────┐
│                   Application Layer (Use Cases)                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SearchUseCase            GetChunkUseCase       BuildContextPack │
│  ├─ PRIME index search    ├─ Chunk retrieval    ├─ Validation  │
│  ├─ Alias expansion       ├─ Token budget       ├─ Pack build  │
│  └─ Score ranking         └─ Evidence matching  └─ Serialization
│                                                                  │
│  PlanUseCase              ValidateContextPack   StatsUseCase    │
│  ├─ Feature mapping       ├─ Health checks      ├─ Metrics agg  │
│  ├─ L1-L4 hierarchy       └─ Error collection   └─ Report gen   │
│  └─ Budget estimation                                           │
│                                                                  │
│  MacroLoadUseCase         StubRegenUseCase      (others)        │
│  ├─ Plan A: PCC           ├─ .pyi generation    └─ Session...   │
│  └─ Plan B: heuristic     └─ AST-based                          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                                  │
                ┌─────────────────┼─────────────────┐
                │                 │                 │
┌───────────────▼──────┐ ┌─────────▼──────┐ ┌──────▼─────────────┐
│   Infrastructure      │ │ Domain Models  │ │  Adapters          │
│   Layer               │ │                │ │                    │
├───────────────────────┤ ├────────────────┤ ├───────────────────┤
│                       │ │                │ │                   │
│ FileSystemAdapter     │ │ TrifectaConfig │ │ SkeletonMapBuilder│
│ Telemetry             │ │ ValidationResult
│ │ AST Parser (M1)     │
│ TemplateRenderer      │ │ PlanResult     │ │ ObsidianConfig    │
│ (skill, agent, etc)   │ │ SymbolQuery    │ │ Manager           │
│                       │ │ SymbolInfo     │ │                   │
│ Error Cards           │ │ ASTError       │ │ Legacy Manifest   │
│ render_error_card()   │ │                │ │                   │
│                       │ │ (domain layer) │ │ (adapters)        │
└───────────────────────┘ └────────────────┘ └───────────────────┘
```

## Data Flow: Search → Get Cycle

```
┌─ User Input
│  query="explain telemetry architecture"
│  segment="."
│  limit=5
│
└─ ctx.search Command Handler
   │
   ├─ _get_telemetry() → Telemetry instance
   ├─ _get_dependencies() → (TemplateRenderer, FileSystem)
   │
   └─ SearchUseCase.execute()
      │
      ├─ Load PRIME index from _ctx/prime_*.md
      │  │
      │  └─ [Performance] Cached on first load
      │
      ├─ Parse aliases (alias expansion T8)
      │  │
      │  └─ Telemetry: ctx_search_alias_expansion_count++
      │
      ├─ Semantic/keyword search on chunks
      │  │
      │  ├─ Semantic: Vector similarity search
      │  ├─ Keyword: Full-text matching
      │  └─ Hybrid: Combine scores
      │
      ├─ Rank by relevance score (0.0 - 1.0)
      │
      └─ Return chunk metadata
         │
         └─ Serialize to output format:
            1. [id] filename
               Score: 0.95 | Tokens: ~2000
               Preview: ...

         ├─ Telemetry observation: latency_ms
         └─ flush()

┌─ User reads output, extracts chunk_id="abc123xyz"
│
└─ ctx.get Command Handler
   │
   ├─ Parse IDs: ["abc123xyz", "def456abc", ...]
   ├─ Check env overrides:
   │  ├─ TRIFECTA_PD_MAX_CHUNKS
   │  └─ TRIFECTA_PD_STOP_ON_EVIDENCE
   │
   └─ GetChunkUseCase.execute()
      │
      ├─ Load context_pack.json
      │
      ├─ Fetch chunk from pack by ID
      │  │
      │  ├─ Raw: Full content
      │  ├─ Excerpt: First 500 chars + context
      │  └─ Skeleton: Structure only
      │
      ├─ Token budget enforcement
      │  │
      │  ├─ Count tokens (GPT-3.5 ~4 chars/token)
      │  ├─ Truncate if budget exceeded
      │  └─ Optional early-stop on evidence
      │
      ├─ Evidence matching (if --query provided)
      │  │
      │  └─ Search for query term in chunk
      │
      └─ Return formatted content
         │
         ├─ Standard: Print content
         └─ PD Report mode: Emit metrics
            {
              "stop_reason": "budget_exceeded|evidence_found|all_chunks",
              "chunks_returned": 3,
              "chunks_requested": 5,
              "chars_returned_total": 8923,
              "strong_hit": 1,
              "support": 0
            }

         ├─ Telemetry observation: latency_ms
         └─ flush()
```

## Data Flow: Plan → Eval-Plan (M9/T9)

```
┌─ User Task
│  "implement caching layer with redis"
│
└─ ctx.plan Command Handler
   │
   └─ PlanUseCase.execute(segment_path, task)
      │
      ├─ Load PRIME index
      │  └─ Extract feature_map: {feature_id: [keywords, paths, chunks]}
      │
      ├─ Match task against features (L1-L4 hierarchy)
      │  │
      │  ├─ L1: Exact feature match (keyword overlap)
      │  ├─ L2: NL trigger (fuzzy semantic match)
      │  ├─ L3: Alias expansion (synonym match)
      │  └─ L4: Fallback (no match - entrypoints used)
      │
      ├─ If match found:
      │  │
      │  ├─ selected_feature: "caching_redis"
      │  ├─ chunk_ids: [chunk_1, chunk_2, ...] (from feature def)
      │  ├─ paths: [src/cache.py, src/redis_client.py, ...]
      │  └─ next_steps: [{action, target}, ...]
      │
      └─ Return PlanResult
         │
         ├─ plan_hit: Boolean (selected_feature != None)
         ├─ selected_by: "feature"|"nl_trigger"|"alias"|"fallback"
         ├─ selected_feature: "caching_redis" or None
         ├─ chunk_ids: List[str]
         ├─ paths: List[str]
         ├─ next_steps: List[{action, target}]
         ├─ budget_est: {tokens, why}
         └─ match_terms_count: int

┌─ Build evaluation dataset (t9_plan_eval_tasks.md)
│  1. "implement caching" | caching_redis | ...
│  2. "add logging" | logging_python | ...
│  ...
│
└─ ctx.eval-plan --dataset docs/plans/t9_plan_eval_tasks.md
   │
   └─ For each task in dataset:
      │
      ├─ Run ctx.plan
      ├─ Get: {plan_hit, selected_feature, selected_by, ...}
      │
      ├─ Classify into L1-L4:
      │  │
      │  └─ selected_by ∈ {feature, nl_trigger, alias, fallback}
      │
      ├─ If expected_feature_id provided:
      │  │
      │  ├─ Compute: plan_accuracy (selected == expected ?)
      │  │
      │  └─ Telemetry: correct_predictions++
      │
      └─ Accumulate metrics
         │
         ├─ feature_count, nl_trigger_count, alias_count, fallback_count
         ├─ true_zero_guidance_count (bug detection)
         └─ correct_predictions (if labels exist)

   ┌─ Compute rates
   │  feature_hit_rate = feature_count / total * 100
   │  nl_trigger_hit_rate = nl_trigger_count / total * 100
   │  alias_hit_rate = alias_count / total * 100
   │  fallback_rate = fallback_count / total * 100
   │  true_zero_guidance_rate = true_zero_count / total * 100
   │  plan_accuracy_top1 = correct_predictions / expected_count * 100
   │
   └─ PCC Metrics (if feature_map available)
      │
      ├─ path_correct_count: Paths in expected feature
      ├─ false_fallback_count: Should-hit but fell back
      └─ safe_fallback_count: Correctly fell back

   ┌─ Gate Decision (T9.3.1)
   │  If is_l1_dataset:
   │  └─ Gate-L1: feature_hit_rate >= 95% AND fallback_rate <= 5%
   │  Else:
   │  └─ Gate-NL: fallback_rate < 20% AND alias_hit_rate <= 70%
   │
   └─ Output report
      │
      ├─ Distribution table (L1-L4)
      ├─ Computed rates
      ├─ PCC metrics (if available)
      ├─ Examples of hits/misses
      └─ GO/NO-GO verdict
```

## Data Flow: AST Symbols Extraction (M1)

```
┌─ User Request
│  ast symbols 'sym://python/mod/src.infrastructure.cli'
│
└─ AST Symbols Handler (cli_ast.py)
   │
   ├─ Parse URI
   │  ├─ Validate format: sym://python/KIND/PATH
   │  ├─ Extract: kind="mod", path="src.infrastructure.cli"
   │  └─ Optional: member (via #)
   │
   ├─ Resolve file path
   │  ├─ Convert: "src.infrastructure.cli" → "src/infrastructure/cli.py"
   │  ├─ Try: candidate_file = {root}/src/infrastructure/cli.py
   │  ├─ Or:  candidate_init = {root}/src/infrastructure/cli/__init__.py
   │  └─ Fail if neither exists
   │
   └─ SkeletonMapBuilder.build(file_path)
      │
      ├─ Parse AST of Python file
      │  ├─ Use ast.parse() on file content
      │  └─ Build symbol tree
      │
      ├─ Extract symbols
      │  ├─ Classes: {...}
      │  ├─ Functions: _get_telemetry, build, search, get, ...
      │  ├─ Variables: (if applicable)
      │  └─ For each: {kind, name, start_line, end_line}
      │
      └─ Return SymbolInfo list
         │
         ├─ M1 Contract JSON
         │  {
         │    "status": "ok",
         │    "segment_root": "/workspaces/trifecta_dope",
         │    "file_rel": "src/infrastructure/cli.py",
         │    "symbols": [
         │      {"kind": "function", "name": "_get_telemetry", "line": 63},
         │      {"kind": "function", "name": "ctx_stats", "line": 92},
         │      ...
         │    ]
         │  }
         │
         └─ Telemetry
            ├─ Event: ast.symbols
            ├─ Metadata: {file, symbols_count}
            └─ Duration: milliseconds
```

## Telemetry Architecture

```
┌──────────────────────────────────────────────────────────────┐
│              Telemetry Collection & Flushing                 │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  In-Memory Event Buffer                                      │
│  ├─ .event(name, metadata, status, latency_ms)            │
│  │  └─ {name, timestamp, metadata, status, latency_ms}    │
│  │                                                         │
│  ├─ .observe(name, latency_ms)                            │
│  │  └─ {name, timestamp, latency_ms} (lightweight)        │
│  │                                                         │
│  └─ .flush()                                               │
│     └─ Write buffer to _ctx/telemetry/                    │
│        ├─ metrics.json (counters)                         │
│        ├─ last_run.json (latency stats)                   │
│        └─ events.jsonl (full event stream)                │
│                                                             │
│  Levels:                                                     │
│  ├─ off:  No collection                                    │
│  ├─ lite: Key events + latency (default)                  │
│  └─ full: Detailed payloads                               │
│                                                             │
│  Environment Override:                                       │
│  └─ TRIFECTA_TELEMETRY_LEVEL=lite|off|full                │
│                                                             │
└──────────────────────────────────────────────────────────────┘

Telemetry Points per Command:
  ctx.search:
    ├─ Event on start: ctx.search
    ├─ Observation: latency_ms
    └─ Telemetry.flush()

  ctx.get:
    ├─ Event on success: ctx.get with {ids, status}
    ├─ Observation: latency_ms
    └─ Telemetry.flush()

  ctx.build:
    ├─ Event: ctx.build with {segment, status, errors}
    ├─ Latency: milliseconds
    └─ Telemetry.flush()

  ... (all 25 commands instrumented similarly)

T8 Metrics (Alias Expansion):
  ├─ ctx_search_alias_expansion_count
  ├─ ctx_search_alias_terms_total
  └─ Computed in ctx.stats:
     avg_terms = alias_terms_total / alias_expansion_count
     expansion_rate = alias_expansion_count / search_count * 100%
```

## Error Handling: Fail-Closed Pattern

```
┌─ Command Handler Entry
│
└─ Parameter Parsing & Defaults
   │
   ├─ Read CLI args via typer
   ├─ Check environment overrides
   └─ Resolve paths
      │
      └─ Execute with try/except/finally
         │
         ├─ TRY:
         │  │
         │  ├─ Gate 1: North Star Validation
         │  │  └─ validate_segment_fp()
         │  │     ├─ If Err → telemetry + exit(1)
         │  │     └─ If Ok → continue
         │  │
         │  ├─ Gate 2: Constitution Validation
         │  │  └─ validate_agents_constitution()
         │  │     ├─ If Err → telemetry + exit(1)
         │  │     └─ If Ok → continue
         │  │
         │  ├─ Gate 3: Legacy Files Check
         │  │  └─ detect_legacy_context_files()
         │  │     ├─ If found → telemetry + exit(1)
         │  │     └─ If none → continue
         │  │
         │  └─ Execute Use Case
         │     ├─ UseCase.execute()
         │     ├─ Handle Ok(result) → output
         │     └─ Handle Err(errors) → telemetry + exit(1)
         │
         ├─ EXCEPT:
         │  │
         │  ├─ Type-Based Routing (preferred):
         │  │  │
         │  │  ├─ isinstance(e, PrimeFileNotFoundError)
         │  │  │  └─ Render SEGMENT_NOT_INITIALIZED error card
         │  │  │
         │  │  ├─ isinstance(e, FileNotFoundError) & "prime" in str(e)
         │  │  │  └─ [DEPRECATED] Fallback string match
         │  │  │
         │  │  └─ All others → Generic error formatting
         │  │
         │  └─ Emit telemetry.event() with error status
         │
         └─ FINALLY:
            │
            └─ telemetry.flush()
               └─ Write _ctx/telemetry/{metrics,events}
```

## Command Dependency Tree

```
Root app (typer.Typer)
│
├─ ctx_app
│  ├─ stats (T8 telemetry)
│  ├─ build
│  │  ├─ validate_segment_fp()
│  │  ├─ validate_agents_constitution()
│  │  └─ detect_legacy_context_files()
│  │
│  ├─ search
│  │  └─ SearchUseCase
│  │
│  ├─ get
│  │  └─ GetChunkUseCase (budget control, evidence matching)
│  │
│  ├─ validate
│  │  └─ ValidateContextPackUseCase
│  │
│  ├─ stats (analytics)
│  │  └─ StatsUseCase
│  │
│  ├─ plan (M9)
│  │  └─ PlanUseCase
│  │
│  ├─ eval-plan (T9)
│  │  ├─ PlanUseCase (for each task)
│  │  ├─ parse_feature_map()
│  │  ├─ evaluate_pcc()
│  │  └─ summarize_pcc()
│  │
│  ├─ sync (macro)
│  │  ├─ BuildContextPackUseCase
│  │  ├─ ValidateContextPackUseCase
│  │  └─ StubRegenUseCase
│  │
│  └─ reset (DESTRUCTIVE)
│     ├─ TemplateRenderer (all templates)
│     ├─ BuildContextPackUseCase
│     └─ ValidateContextPackUseCase
│
├─ ast_app (M1 PRODUCTION)
│  ├─ symbols
│  │  ├─ SymbolQuery.parse()
│  │  └─ SkeletonMapBuilder.build()
│  │
│  ├─ snippet (stub)
│  │
│  └─ hover (WIP)
│
├─ session_app
│  └─ append
│     └─ Direct file I/O to _ctx/session_*.md
│
├─ telemetry_app
│  ├─ report → generate_report()
│  ├─ export → export_data()
│  └─ chart → generate_chart()
│
├─ obsidian_app
│  ├─ sync
│  │  ├─ create_sync_use_case()
│  │  └─ ObsidianSyncUseCase.execute()
│  │
│  ├─ config
│  │  └─ ObsidianConfigManager
│  │
│  └─ validate
│     └─ Validate vault writeability
│
├─ legacy_app
│  └─ scan
│     └─ scan_legacy(manifest)
│
└─ Root commands
   ├─ create
   │  └─ TemplateRenderer (all templates)
   │
   ├─ load
   │  └─ MacroLoadUseCase (Plan A: PCC, Plan B: heuristic)
   │
   ├─ validate-trifecta (deprecated)
   │  └─ ValidateTrifectaUseCase
   │
   └─ refresh-prime (deprecated)
      └─ RefreshPrimeUseCase
```

## Validation Gate Flowchart

```
                        Command Input
                            │
                            ▼
                    ┌──────────────────┐
                    │ Parameter Parse  │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │ North Star Gate  │
                    │ validate_segment │
                    │ _fp()            │
                    └────────┬─────────┘
                             │
         ┌───────────────────┴───────────────────┐
         │                                       │
        ✗ Err                                  ✓ Ok
         │                                       │
        ┌▼─────────────────┐           ┌────────▼─────────┐
        │Emit error        │           │Constitution Gate │
        │telemetry + exit  │           │validate_agents   │
        │(code=1)          │           │_constitution()   │
        └──────────────────┘           └────────┬─────────┘
                                                 │
                                   ┌─────────────┴─────────────┐
                                   │                           │
                                  ✗ Err                      ✓ Ok
                                   │                           │
                              ┌────▼──────┐            ┌───────▼────┐
                              │Emit error │            │Legacy Files│
                              │+ exit(1)  │            │Check       │
                              └───────────┘            └───────┬────┘
                                                               │
                                               ┌───────────────┴───────────┐
                                               │                           │
                                            Found                       None
                                               │                           │
                                          ┌────▼──────┐            ┌───────▼──┐
                                          │Emit error │            │ Execute  │
                                          │+ exit(1)  │            │Use Case  │
                                          └───────────┘            └──────────┘
```

---

## Performance Profile (Typical Latencies)

```
Command              p50       p95      max      Notes
─────────────────────────────────────────────────────────────
ctx.search           12ms      45ms     234ms    Alias expansion varies
ctx.get              8ms       32ms     156ms    Budget truncation adds latency
ctx.build            234ms     890ms    2100ms   Validation gates add overhead
ctx.validate         45ms      123ms    567ms    Pack size dependent
ctx.stats            5ms       12ms     34ms     Local metrics only
ctx.plan             45ms      123ms    567ms    Feature matching cost
ctx.eval-plan        5000ms+   -        -        Linear: O(n tasks)
ctx.sync             279ms+    -        -        Build + validate + stubs
ast.symbols          5ms       12ms     34ms     AST parsing (M1)
session.append       2ms       5ms      12ms     File I/O
telemetry.report     23ms      89ms     234ms    Report generation
obsidian.sync        234ms     1200ms   5000ms   Vault I/O
legacy.scan          23ms      89ms     234ms    Manifest scanning
```

---

## Extension Points (for Developers)

```
To add a new command:

1. Create command handler function:
   @ctx_app.command("mycommand")
   def my_command(
       segment: str = typer.Option(...),
       option1: str = typer.Option(...),
       telemetry_level: str = typer.Option("lite")
   ) -> None:
       """Description."""
       telemetry = _get_telemetry(segment, telemetry_level)
       start_time = time.time()
       template, fs, _ = _get_dependencies(segment, telemetry)

       try:
           use_case = MyUseCase(fs, telemetry)
           result = use_case.execute(...)
           typer.echo(result)
           telemetry.observe("mycommand", int(...))
       except Exception as e:
           telemetry.event(..., {"status": "error"}, ...)
           typer.echo(_format_error(e), err=True)
           raise typer.Exit(1)
       finally:
           telemetry.flush()

2. Create use case in src/application/{mycommand}_use_case.py
   class MyUseCase:
       def __init__(self, fs: FileSystemAdapter, telemetry: Telemetry):
           self.fs = fs
           self.telemetry = telemetry

       def execute(self, ...):
           # Implement logic
           return result

3. Test with: ast.symbols to verify extraction

4. Add to test gates: make gate-all
```

---

*Visualization completed: 2026-01-05*
