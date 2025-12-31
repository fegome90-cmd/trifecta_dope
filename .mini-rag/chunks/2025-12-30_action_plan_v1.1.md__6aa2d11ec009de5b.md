### Why Defer?

**Reason 1: Limited ROI for Segment-Local Search**
- Trifecta is segment-local, not global
- Segments are small (~7K tokens for trifecta_dope)
- Lexical search "good enough" for small sets

**Reason 2: Progressive Disclosure Changes Everything**
- v2 roadmap: AST-based context (code symbols, not docs)
- LSP integration (IDE-native context)
- Both make lexical search irrelevant

**Reason 3: MVP is Already Operational**
- 99.9% token precision
- <5s per cycle
- 100% budget compliance
- No critical issues
