def extract_anchors(query: str, anchors_cfg: dict, aliases_cfg: dict) -> dict:
    """
    Pure logic extractor for anchors and aliases.
    Args:
        query: Raw input query string.
        anchors_cfg: Loaded anchors.yaml dict.
        aliases_cfg: Loaded aliases.yaml dict (wrapper 'aliases' key handled if present).

    Returns:
        dict with tokens, strong, weak, aliases_matched lists.
    """

    # Normalize query
    query_lower = query.lower()

    # Tokenize: split by whitespace and strip basic punctuation
    # Keep it simple and deterministic as requested
    raw_tokens = query_lower.split()
    tokens = []
    for t in raw_tokens:
        clean_t = t.strip(".,;:()[]{}\"'")  # Corrected escaping for " and '
        if clean_t:
            tokens.append(clean_t)

    strong_found = []
    weak_found = []
    aliases_matched = []

    # Load config parts safely
    strong_cfg = anchors_cfg.get("anchors", {}).get("strong", {})
    weak_cfg = anchors_cfg.get("anchors", {}).get("weak", {})

    # Flatten strong candidates
    strong_candidates = (
        strong_cfg.get("files", [])
        + strong_cfg.get("dirs", [])
        + strong_cfg.get("exts", [])
        + strong_cfg.get("symbols_terms", [])
    )

    # Flatten weak candidates
    weak_candidates = weak_cfg.get("intent_terms", []) + weak_cfg.get("doc_terms", [])

    # 1. Detect Strong (exact substring in tokens or query)
    # Actually, mandate says "detect strong por substring exacto".
    # Checking if candidate is in query string is safest for things like "agent.md"
    for cand in strong_candidates:
        if cand in query_lower:
            strong_found.append(cand)

    # 2. Detect Weak (usually single terms, check tokens)
    for cand in weak_candidates:
        if (
            cand in tokens
        ):  # Exact token match often better for common words, but mandate implies substring logic for aliases.
            # Let's use token match for weak terms to avoid over-matching inside other words
            weak_found.append(cand)
        # Fallback: if multi-word weak term exists (unlikely in current config but possible), check substring
        elif " " in cand and cand in query_lower:
            weak_found.append(cand)

    # 3. Detect Aliases
    # aliases_cfg might be list or dict with 'aliases' key
    alias_list = aliases_cfg.get("aliases", []) if isinstance(aliases_cfg, dict) else aliases_cfg

    for entry in alias_list:
        phrase = entry["phrase"].lower()
        if phrase in query_lower:
            aliases_matched.append(phrase)
            # Add alias anchors to strong list
            for added in entry.get("add_anchors", []):
                strong_found.append(added.lower())

    # Dedupe lists preserving order
    def dedupe(seq):
        seen = set()
        result = []
        for x in seq:
            if x not in seen:
                seen.add(x)
                result.append(x)
        return result

    return {
        "tokens": tokens,
        "strong": dedupe(strong_found),
        "weak": dedupe(weak_found),
        "aliases_matched": dedupe(aliases_matched),
    }
