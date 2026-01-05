──────────────────────────────────────────────────────────
                    trifecta ctx build       use_cases.py             BuildContextPackUseCase
                    trifecta ctx search      search_get_usecases.py   SearchUseCase → ContextService
                    trifecta ctx get         search_get_usecases.py   GetChunkUseCase → ContextService
                    trifecta load            use_cases.py             MacroLoadUseCase (Plan A/B)
                    trifecta session append  use_cases.py             SessionAppendUseCase
                    trifecta ctx stats       cli.py (direct)          Telemetry JSON read
                    trifecta eval plan (v1.1) pcc_metrics.py          parse_feature_map + evaluate_pcc
```
