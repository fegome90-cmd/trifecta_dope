### What changes in practice

Your `ctx.search` no longer searches just text—it searches symbols.

Progressive disclosure levels:

- **L0 Skeleton**: signatures, classes, functions (0 tokens upfront)
- **L1 Symbol**: exact node via LSP `documentSymbols`, `definition`, `references`
- **L2 Window**: lines around a symbol (controlled radius)
- **L3 Raw**: last resort

The agent requests a function definition instead of the entire file.
