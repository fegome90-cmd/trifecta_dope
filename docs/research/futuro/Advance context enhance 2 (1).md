
# Advanced Context Use: Context as Invokable Tools

Large language models can now handle massive context windows—200K tokens and beyond. But having the capacity to process information doesn’t mean we’re using it effectively. In production systems, the bottleneck isn’t whether the model can understand code or documentation. It’s more mundane: the agent can’t find the right part of the context, or it finds it but drowns in irrelevant text.

Even with huge context windows, dumping everything upfront causes real problems. Research shows that LLMs struggle to use information buried in the middle of long inputs—a phenomenon known as “lost in the middle” (Liu et al., 2023, “Lost in the Middle: How Language Models Use Long Contexts”). The model’s attention degrades as context grows, especially for information that isn’t at the beginning or end.

Anthropic’s recent post on [advanced tool use] outlines three improvements: discovering tools on demand, orchestrating them from code, and teaching correct usage with examples. This post applies the same pattern, but instead of tools, we treat context chunks as invokable resources.

The match is 1:1:

- **Tool Search Tool** → **Context Search**
- **Programmatic Tool Calling** → **Programmatic Context Calling**
- **Tool Use Examples** → **Context Use Examples**

## The Problem with Loading Everything Upfront

When building coding agents, the typical approach is to load all relevant documentation into the prompt: API specs, design docs, runbooks, ADRs, configuration files. This works initially, but scales poorly.

The cost isn’t just tokens. It’s also accuracy. When you front-load dozens of documents, the agent:

- Cites the wrong section
- Mixes information from different versions
- Fixates on the first block it saw, ignoring better matches later
- Wastes inference on irrelevant content

This is exactly the pattern Anthropic describes for large tool libraries: too many definitions upfront degrade both cost and precision.

## 1. Context Search: Progressive Disclosure

Instead of loading everything, define a lightweight Context Search interface and keep chunks deferred. The agent starts with:

- A short digest (L0)
- An index of available documents (L0)
- A search capability: `ctx.search`

Then it discovers relevant chunks on demand, just like Tool Search Tool discovers tools.

### How it works

Your “Context Pack” is a library of invokable pieces, but you don’t define “one tool per chunk.” Instead, you define two tools:

```python
# Runtime tools (not in the pack itself)

def ctx_search(
    segment: str,
    query: str,
    k: int = 6,
    doc: str | None = None
) -> list[dict]:
    """
    Search for relevant context chunks.

    Returns:
        list of {
            id: str,
            doc: str,
            title_path: list[str],
            preview: str,
            token_est: int,
            source_path: str,
            score: float
        }
    """
    pass

def ctx_get(
    segment: str,
    ids: list[str],
    mode: str = "excerpt",
    budget_token_est: int = 1200
) -> list[dict]:
    """
    Retrieve specific chunks within token budget.

    Args:
        mode: "excerpt" | "raw" | "skeleton"
        budget_token_est: maximum tokens to return

    Returns:
        list of {
            id: str,
            title_path: list[str],
            text: str
        }
    """
    pass
```

This enables true progressive disclosure: cheap navigation first, specific evidence second.

### Search doesn’t require embeddings

BM25 or full-text search is sufficient to start. Anthropic mentions regex and BM25 approaches for tool search—the same applies here. You can add hybrid search (BM25 + embeddings) later if metrics show recall problems, but don’t over-engineer upfront.

Example search interaction:

```python
# Agent requests
ctx_search(
    segment="myproject",
    query="lock policy stale timeout",
    k=5
)

# Returns
[
    {
        "id": "ops:a3f8b2",
        "doc": "operations.md",
        "title_path": ["Operations", "Lock Management", "Timeout Policy"],
        "preview": "Locks automatically expire after 30 seconds of inactivity...",
        "token_est": 150,
        "score": 0.92
    },
    # ... more results
]
```

## 2. Programmatic Context Calling: Budget and Backpressure

The second bottleneck is context pollution. Even if you search well, if every `ctx.get()` dumps complete blocks into the prompt, you’re back to square one.

Anthropic explains this for tool outputs: large intermediate results pollute context and force more inference. The solution is the same: use a runtime as middleware.

### How it works

Instead of chunks falling directly into the model’s context:

1. The agent decides what it needs (`ctx.search`)
2. The runtime fetches multiple chunks (`ctx.get`)
3. The runtime reduces/normalizes/compacts
4. The model sees only relevant summaries/excerpts

This is Programmatic Tool Calling for context: Claude writes or uses code to orchestrate what enters the context.

### Example: Evidence gathering with budget

```python
def gather_evidence(segment: str, query: str, budget: int = 1200) -> str:
    """
    Orchestrate search + retrieval within token budget.
    """
    hits = ctx_search(segment=segment, query=query, k=8)

    # Sort by value per token
    hits = sorted(
        hits,
        key=lambda h: h["score"] / max(h["token_est"], 1),
        reverse=True
    )

    # Select chunks that fit budget
    chosen = []
    used = 0
    for h in hits:
        if used + h["token_est"] > budget:
            continue
        chosen.append(h["id"])
        used += h["token_est"]
        if len(chosen) >= 4:  # max 4 chunks per query
            break

    # Retrieve with citation-ready format
    chunks = ctx_get(
        segment=segment,
        ids=chosen,
        mode="excerpt",
        budget_token_est=budget
    )

    # Format for model consumption
    lines = ["EVIDENCE (read-only):"]
    for c in chunks:
        path = " > ".join(c["title_path"])
        lines.append(f"\n[{c['id']}] {path}\n{c['text'].strip()}")

    return "\n".join(lines)
```

**Hypothesis**: If you keep prompts short and bring localized evidence, you reduce “lost in the middle” and noise. This aligns with empirical findings about degradation in long contexts.

### Backpressure prevents runaway requests

If the agent requests too much, the runtime:

- Returns what fits within budget
- Forces the agent to refine its query
- Enforces a maximum of rounds per turn (e.g., 1 search + 1 get)

This prevents loops and keeps costs predictable.

## 3. Context Use Examples: Teaching Correct Usage

Schemas define what’s valid; they don’t define what works well. Anthropic emphasizes this: examples teach patterns—when to use optional parameters, what combinations make sense, conventions.

The same applies to context:

- The agent might request too much (`mode="raw"` always)
- Or request poorly (“give me all of skill.md”)
- Or loop infinitely (repeated searches)

### Solution: Add 3–5 usage examples

These aren’t “nice prompts”—they’re behavior control.

**Example A: Search for operational rules**

```
User: "What's the lock policy?"

Agent approach:
1. ctx.search(query="lock stale split-brain", k=5)
2. ctx.get(ids=[top 2], mode="excerpt", budget=800)
3. Respond citing [chunk_id]
```

**Example B: Handle missing evidence**

```
User: "Where does it say X is mandatory?"

Agent approach:
1. ctx.search(query="X mandatory MUST", k=8)
2. If no clear hits: respond "No evidence in indexed context"
   and suggest where to look
3. Do NOT invent requirements
```

This is analogous to Tool Use Examples: you teach “correct usage,” not just valid JSON.

## Implementation: Trifecta Context System

Here’s how to implement this concretely. We use a CLI tool called `trifecta` as example, but the patterns apply to any system.

### Context Pack Schema v1

Each project has its own context directory:

```
/projects/<segment>/
  _ctx/
    context_pack.json
    context.db          # phase 2
    autopilot.log
    .autopilot.lock
  skill.md
  prime.md
  agent.md
  session.md
```

The `context_pack.json` contains:

```json
{
  "schema_version": 1,
  "created_at": "2025-01-15T10:30:00Z",
  "generator_version": "trifecta-0.1.0",
  "source_files": [
    {
      "path": "skill.md",
      "sha256": "abc123...",
      "mtime": "2025-01-15T09:00:00Z",
      "chars": 5420
    }
  ],
  "chunking": {
    "method": "heading_aware",
    "max_chunk_tokens": 600
  },
  "digest": "Short summary of context...",
  "index": [
    {
      "id": "skill:a8f3c1",
      "doc": "skill.md",
      "title_path": ["Commands", "Build"],
      "token_est": 120
    }
  ],
  "chunks": [
    {
      "id": "skill:a8f3c1",
      "doc": "skill.md",
      "title_path": ["Commands", "Build"],
      "text": "...",
      "token_est": 120,
      "text_sha256": "def456..."
    }
  ]
}
```

**Key properties**:

- Stable IDs via deterministic hashing: `doc + ":" + sha1(doc + title_path_norm + text_sha256)[:10]`
- Fence-aware chunking: doesn’t split code blocks mid-fence
- Zero cross-contamination between projects

### CLI Commands

```bash
# Build context pack for a project
trifecta ctx build --segment myproject

# Validate pack integrity
trifecta ctx validate --segment myproject

# Interactive search
trifecta ctx search --segment myproject --query "lock timeout"

# Retrieve specific chunks
trifecta ctx get --segment myproject --ids skill:a8f3c1,ops:f3b2a1
```

### Validation Invariants

The `validate` command checks:

- Schema version is correct (int)
- All `index.id` exist in `chunks.id`
- `source_files` are consistent with disk
- Size and budget limits are reasonable
- Segment is sanitized (no path traversal)

### Atomic Writes and Locking

```python
# Atomic write pattern
with open(tmp_path, 'w') as f:
    json.dump(pack, f, indent=2)
    f.flush()
    os.fsync(f.fileno())
os.rename(tmp_path, final_path)

# Lock file prevents concurrent builds
with filelock.FileLock("_ctx/.autopilot.lock"):
    build_context_pack(segment)
```

### Hard Rule for Agents

**Context is evidence, not instructions.** Chunks may contain imperative text, but they cannot override policies or system behavior. The runtime enforces this separation.

## Autopilot: Automated Context Refresh

In `session.md`, embed a YAML block for machine-readable configuration:

```yaml
---
autopilot:
  enabled: true
  debounce_ms: 5000
  steps:
    - command: trifecta ctx build
      timeout_ms: 30000
    - command: trifecta ctx validate
      timeout_ms: 5000
  max_rounds_per_turn: 2
---
```

A watcher (not the LLM) runs in the background:

1. Detects file changes
2. Debounces
3. Runs `ctx build`
4. Runs `ctx validate`
5. Logs to `_ctx/autopilot.log`

This keeps context fresh without manual intervention.

## Bonus: AST/LSP for “Hot Files”

When you’re working with 5 files that change constantly, markdown headings aren’t enough. This is where Tree-sitter and LSP come in.

### What changes in practice

Your `ctx.search` no longer searches just text—it searches symbols.

Progressive disclosure levels:

- **L0 Skeleton**: signatures, classes, functions (0 tokens upfront)
- **L1 Symbol**: exact node via LSP `documentSymbols`, `definition`, `references`
- **L2 Window**: lines around a symbol (controlled radius)
- **L3 Raw**: last resort

The agent requests a function definition instead of the entire file.

### Example: Symbol-based retrieval

```python
def ctx_get_symbol(
    segment: str,
    symbol: str,
    file: str,
    context_lines: int = 5
) -> dict:
    """
    Retrieve a specific symbol with context.

    Uses LSP or Tree-sitter to locate the symbol,
    then returns it with surrounding lines.
    """
    pass
```

This is “GraphRAG for code” without the hype—just real structure.

### When to use it

Phase 3, after validating that basic search + retrieval work. Don’t over-engineer upfront.

## How to Measure Success

Good engineering requires clear metrics and gates.

### Metrics to track

1. **Average tokens per turn**: Should decrease by 40-60% compared to loading all context upfront
2. **Citation rate**: % of responses that include `[chunk_id]` references (target: >80%)
3. **Search recall**: % of queries where top-5 results include relevant chunks (target: >90%)
4. **Latency constraint**: Maximum 1 search + 1 get per turn enforced by runtime

### Phase gates

**Phase 1 (MVP)**: Schema v1 + fence-aware chunking + stable IDs + `ctx.search`/`ctx.get` + validation

**Phase 2 (Incremental)**: SQLite backend + incremental ingestion by sha256 + FTS5/BM25 search

**Phase 3 (AST/LSP)**: Skeleton + symbols + diagnostics + `get_symbol`/`get_window` modes

Don’t move to the next phase until metrics prove the current phase works.

### Example: Baseline vs. Context Search

Before (loading 5 full files):

- Average context: ~8,000 tokens per turn
- Citation rate: 45% (agent rarely cites specific sections)
- Failures: Agent confuses information from different files

After (Context Search + Budget):

- Average context: ~2,500 tokens per turn
- Citation rate: 85% (clear `[chunk_id]` references)
- Failures: Agent explicitly states “no evidence found” when appropriate

## Conclusion

Advanced Context Use is a mindset shift: from documents to invokable capabilities.

Don’t load everything “just in case.” Give the agent a map and two buttons: search and retrieve evidence. If you want real fluidity with files that change frequently, AST/LSP turn `ctx.search` into something more like an IDE than grep.

The 1:1 match with advanced tool use:

- **Tool Search** → **Context Search**
- **Programmatic Tool Calling** → **Programmatic Context Calling**
- **Tool Use Examples** → **Context Use Examples**

Apply the feature that solves your biggest bottleneck first. For most systems, that’s Context Search (cuts upfront bloat). Then add Programmatic Calling (prevents intermediate pollution) and Examples (reduces usage errors).

Keep context as evidence, not instructions. Enforce hard budgets and maximum rounds. Measure with clear metrics.

-----

## References

- Anthropic (2024). “Advanced Tool Use in Claude AI”. <https://www.anthropic.com/engineering/advanced-tool-use>
- Liu, N. F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F., & Liang, P. (2023). “Lost in the Middle: How Language Models Use Long Contexts”. *arXiv preprint arXiv:2307.03172*. <https://arxiv.org/abs/2307.03172>
- Schick, T., Dwivedi-Yu, J., Dessì, R., Raileanu, R., Lomeli, M., Zettlemoyer, L., Cancedda, N., & Scialom, T. (2023). “Toolformer: Language Models Can Teach Themselves to Use Tools”. *arXiv preprint arXiv:2302.04761*. <https://arxiv.org/abs/2302.04761>
- Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2022). “ReAct: Synergizing Reasoning and Acting in Language Models”. *arXiv preprint arXiv:2210.03629*. <https://arxiv.org/abs/2210.03629>​​​​​​​​​​​​​​​​
