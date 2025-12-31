## Key Concepts

**Clean Architecture:**
```
src/
├── domain/          # PURE - no IO, no tree-sitter
│   ├── entities/    # ASTNode, Symbol, ImportStatement ✅
│   └── ports/       # IParser, ILanguageParser, ISymbolExtractor ✅
├── infrastructure/  # IO, tree-sitter
│   ├── parsers/     # TreeSitterParser, LanguageParsers ✅
│   └── extractors/  # SymbolExtractor ✅
├── application/     # Orchestrates domain + infrastructure
│   └── services/    # ASTService ✅
└── interfaces/      # Public API ✅
```
```

**Step 3: Extract allowlisted paths**

```bash
$ grep -n "src/" /Users/felipe_gonzalez/Developer/AST/_ctx/prime_ast.md | head -20
29:src/
71:- ✅ Integration tests (src/integration/integration.test.ts)
```

**Allowlisted paths from prime:**
- `src/domain/entities/`
- `src/domain/ports/`
- `src/infrastructure/parsers/`
- `src/infrastructure/extractors/`
- `src/application/services/`
- `src/interfaces/`
- `src/integration/integration.test.ts`

**Step 4: Open ONLY allowlisted file**

```bash
