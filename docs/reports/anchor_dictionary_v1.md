# Anchor Dictionary v1 (Phase 2)

**Component**: `src/domain/anchor_extractor.py` (Pure Logic)
**Configuration**: `configs/anchors.yaml`, `configs/aliases.yaml`
**Status**: Verified (PASS)

## Concepts

*   **Anchor Strong**: A precise identifier (filename, directory, extension, reserved symbol) that implies a specific context target.
    *   *Examples*: `agent.md`, `docs/`, `class`
*   **Anchor Weak**: A term indicating intent or document type, used to boost relevance or guide fallback.
    *   *Examples*: `template`, `guía`, `how-to`
*   **Alias**: A natural language phrase mapped to one or more strong/weak anchors. Used for "Switchboard" expansion.
    *   *Example*: "session persistence" -> `session.md`

**Note**: Score is calculated downstream based on these matches, but is **NOT used as a strict gate** in this phase. The Extractor provides the raw signals.

## Dictionary Summary

*   **Strong Anchors**:
    *   Files: 7 (`agent.md`, `session.md`, ...)
    *   Dirs: 5 (`docs/`, `src/`, ...)
    *   Exts: 5 (`.md`, `.py`, ...)
    *   Symbols: 5 (`class`, `def`, ...)
*   **Weak Anchors**:
    *   Intent: 10 (`template`, `example`, ...)
    *   Doc: 10 (`guía`, `manual`, ...)
*   **Aliases**: 16 entries (including Spanish support).

## Examples (Input -> Output)

### 1. Direct File Reference
**Query**: "check agent.md template"
**Output**:
```json
{
  "strong": ["agent.md"],
  "weak": ["template"],
  "aliases_matched": []
}
```

### 2. Spanish NL Alias
**Query**: "cómo configurar obsidian"
**Output**:
```json
{
  "strong": ["obsidian config", "obsidian"],
  "weak": ["cómo"],
  "aliases_matched": ["configurar obsidian"]
}
```

### 3. Complex Intent
**Query**: "implement session persistence protocol"
**Output**:
```json
{
  "strong": ["session.md", "session append"],
  "weak": ["protocolo"],
  "aliases_matched": ["session persistence"]
}
```

### 4. Technical Symbol
**Query**: "def extract_anchors"
**Output**:
```json
{
  "strong": ["def"],
  "weak": [],
  "aliases_matched": []
}
```

### 5. Legacy Reference
**Query**: "legacy scan results"
**Output**:
```json
{
  "strong": ["legacy", "manifest"],
  "weak": [],
  "aliases_matched": ["legacy scan"]
}
```
