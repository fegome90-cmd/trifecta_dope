## 3. Selector DSL Contract (`sym://`)

To eliminate ambiguity between module paths vs. class names, we enforce **Option A (Explicit Prefixes)**.

The Selector URI MUST conform to the following EBNF grammar. Invalid URIs MUST be rejected immediately with `INVALID_SELECTOR_SYNTAX`.
