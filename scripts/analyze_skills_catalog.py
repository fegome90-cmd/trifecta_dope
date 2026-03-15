from __future__ import annotations

import csv
import itertools
import re
from dataclasses import dataclass, replace
from pathlib import Path

BASE_CSV = Path("data/skills_catalog/skills_catalog.csv")
OUT_CSV = Path("data/skills_catalog/skills_catalog_enriched.csv")
OUT_REPORT = Path("docs/reports/skills_trigger_collision_report.md")

FAMILY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "review-security-verification-debug",
        ("security", "debug", "verify", "verification", "review", "audit", "feedback", "ci"),
    ),
    (
        "backend-python-testing-standards",
        ("backend", "python", "pytest", "testing", "tdd", "standards", "sqlite", "postgres", "sql", "database", "pgvector"),
    ),
    (
        "search-exploration-retrieval",
        ("search", "explore", "exploration", "fetch", "retrieve", "retrieval", "codebase", "grep", "context7", "brave", "web-search"),
    ),
    (
        "frontend-design-ui",
        ("frontend", "react", "ui", "design", "glass", "clay", "neubrutalism", "liquid", "webapp", "accessibility"),
    ),
    ("git-pr-workflow", ("git", "github", "pull", "pr", "reviewctl", "branch", "worktree", "commit", "push")),
    (
        "docs-formats",
        ("doc", "docx", "pptx", "xlsx", "pdf", "document", "presentation", "slides", "spreadsheet", "internal-comms"),
    ),
    (
        "ai-rag-data-db",
        ("rag", "embedding", "semantic", "vector", "llm", "ml", "telemetry", "eval", "chunk", "cache"),
    ),
    ("meta-pi-trifecta", ("skill", "skills", "pi", "trifecta", "tmux", "checkpoint", "agent", "workorder", "graph", "extension")),
)

INTENT_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("review", ("review", "audit", "check", "assess")),
    ("debug", ("debug", "debugging", "error", "errors", "crash", "crashes", "failure", "troubleshoot")),
    ("verify", ("verify", "verification", "validate", "validation", "gate", "gates", "quality")),
    ("implement", ("implement", "implementing", "build", "building", "create", "creating", "generate", "remediate", "setup")),
    ("test", ("test", "tests", "testing", "pytest", "coverage", "eval")),
    ("search", ("search", "explore", "find", "fetch", "retrieve", "query")),
    ("design", ("design", "style", "guideline", "guidelines", "ui", "frontend", "theme")),
    ("operate", ("ops", "workflow", "cli", "command", "commands", "calendar", "drive", "gmail")),
)

ARTIFACT_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("code", ("code", "repo", "backend", "python", "react", "reviewctl")),
    ("document", ("doc", "docx", "pdf", "documentation", "memo", "report")),
    ("presentation", ("pptx", "slides", "presentation", "deck")),
    ("spreadsheet", ("xlsx", "csv", "spreadsheet", "tsv")),
    ("browser-web", ("browser", "web", "playwright", "ui", "site")),
    ("database", ("sql", "sqlite", "postgres", "pgvector", "database")),
    ("skill-system", ("skill", "skills", "pi", "trifecta", "agent")),
    ("workflow", ("workflow", "git", "pr", "branch", "commit", "push", "checkpoint", "tmux")),
)

PHASE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("discovery", ("search", "explore", "find", "fetch", "discover", "discovery")),
    ("implementation", ("implement", "implementing", "build", "building", "create", "creating", "generate", "setup", "remediate")),
    ("testing", ("test", "tests", "testing", "pytest", "coverage", "eval")),
    ("review", ("review", "audit", "feedback")),
    ("verification", ("verify", "verification", "validate", "validation", "gate", "gates", "quality", "typecheck", "lint")),
    ("delivery", ("commit", "push", "pr", "publish", "handoff")),
)

PRIORITY_LOTS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (
        "L1-review-security-verification-debug",
        ("security-review", "debug-helper", "verification-loop", "learned-pr-feedback-resolution", "branch-review-api"),
        "High confusion risk in quality, review, security, and failure-analysis prompts.",
    ),
    (
        "L2-search-exploration-retrieval",
        ("cli-explorer", "codebase-explorer", "rctl-explore", "web-search", "web-fetch", "brave-search", "context7"),
        "Discovery tasks can route to the wrong search surface or wrong depth of analysis.",
    ),
    (
        "L3-backend-python-testing",
        ("backend-implementation-patterns", "python-patterns", "python-testing", "tdd-workflow", "coding-standards", "python-cli-patterns"),
        "Implementation and language/testing guidance overlap on common developer prompts.",
    ),
    (
        "L4-docs-formats",
        ("docx", "pptx", "xlsx", "doc-coauthoring", "nutrient-document-processing", "internal-comms"),
        "Document intent often overlaps with file-format-specific execution skills.",
    ),
    (
        "L5-frontend-design-ui",
        ("frontend-patterns", "frontend-design", "web-design-guidelines", "vercel-react-best-practices", "vercel-composition-patterns"),
        "Frontend implementation, design, and UI review often share vocabulary but require distinct execution.",
    ),
)

BOUNDARY_MARKERS: tuple[str, ...] = (
    "do not use",
    "don't use",
    "dont use",
    "not for",
    "not when",
    "not if",
    "prefer this over",
    "prefer this for",
    "use this over",
    "use this instead",
    "use it instead",
    "rather than",
    "instead of",
    "outside reviewctl",
    "outside the repo",
    "outside the codebase",
    "only use",
    "only when",
    "only if",
    "specifically",
    "explicitly",
    "requires",
)

REDIRECT_MARKERS: tuple[str, ...] = (
    "use ",
    "prefer this over",
    "instead",
    "instead of",
    "rather than",
)


@dataclass(frozen=True)
class SkillRow:
    row: dict[str, str]
    trigger_terms: frozenset[str]
    trigger_phrases: frozenset[str]
    brief_terms: frozenset[str]
    text_terms: frozenset[str]
    text_blob: str
    family: str
    primary_intent: str
    artifact_focus: str
    workflow_phase: str
    specificity_hint: str
    boundary_clauses: tuple[str, ...]
    boundary_marker_count: int
    explicit_boundary_targets: tuple[str, ...]
    explicit_prefer_targets: tuple[str, ...]
    boundary_strength: float


@dataclass(frozen=True)
class Collision:
    left: str
    right: str
    severity: str
    score: float
    raw_score: float
    boundary_penalty: float
    family_match: bool
    artifact_match: bool
    phase_match: bool
    overlap_count: int
    overlap_terms: tuple[str, ...]
    rationale: str


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_pipe_set(value: str) -> frozenset[str]:
    if not value.strip():
        return frozenset()
    return frozenset(part.strip() for part in value.split("|") if part.strip())


def tokenize_text(*values: str) -> frozenset[str]:
    tokens: set[str] = set()
    for value in values:
        normalized = value.lower().replace("-", " ").replace("_", " ").replace("/", " ")
        for token in re.findall(r"[a-z0-9][a-z0-9+.:-]*", normalized):
            cleaned = token.strip(".:+")
            if len(cleaned) >= 3:
                tokens.add(cleaned)
    return frozenset(tokens)


def normalize_text_blob(*values: str) -> str:
    joined = " ".join(values).lower()
    cleaned = re.sub(r"[`\"'()\[\]{}]", " ", joined)
    cleaned = cleaned.replace("/", " ").replace("_", " ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return f" {cleaned.strip()} "


def keyword_matches(keyword: str, text_terms: frozenset[str], text_blob: str) -> bool:
    normalized = normalize_whitespace(keyword.lower().replace("-", " ").replace("/", " "))
    if not normalized:
        return False
    if " " in normalized:
        return f" {normalized} " in text_blob or normalized in text_blob
    if normalized in text_terms:
        return True
    if normalized.endswith("s") and normalized[:-1] in text_terms:
        return True
    plural = f"{normalized}s"
    if plural in text_terms:
        return True
    if len(normalized) >= 5 and any(term.startswith(normalized) for term in text_terms):
        return True
    return f" {normalized} " in text_blob


def classify_from_rules(
    text_terms: frozenset[str],
    text_blob: str,
    rules: tuple[tuple[str, tuple[str, ...]], ...],
    default: str,
) -> str:
    best_label = default
    best_score = 0
    for label, keywords in rules:
        score = sum(1 for keyword in keywords if keyword_matches(keyword, text_terms, text_blob))
        if score > best_score:
            best_label = label
            best_score = score
    return best_label


def collect_boundary_clauses(text: str) -> tuple[str, ...]:
    clauses: list[str] = []
    raw_clauses = re.split(r"[.;\n]+", text)
    for clause in raw_clauses:
        cleaned = normalize_whitespace(clause)
        lowered = cleaned.lower()
        if not cleaned:
            continue
        if any(marker in lowered for marker in BOUNDARY_MARKERS):
            clauses.append(cleaned)
    return tuple(clauses)


def strip_boundary_clauses(text: str) -> str:
    kept: list[str] = []
    raw_clauses = re.split(r"[.;\n]+", text)
    for clause in raw_clauses:
        cleaned = normalize_whitespace(clause)
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if any(marker in lowered for marker in BOUNDARY_MARKERS):
            continue
        kept.append(cleaned)
    return normalize_whitespace(". ".join(kept))


def clause_has_redirect(clause: str) -> bool:
    lowered = clause.lower()
    return any(marker in lowered for marker in REDIRECT_MARKERS)


def slug_aliases(slug: str) -> tuple[str, ...]:
    spaced = slug.replace("-", " ").replace("_", " ")
    aliases = {slug.lower(), spaced.lower()}
    return tuple(sorted(alias for alias in aliases if len(alias) >= 4))


def clause_references_slug(clause: str, slug: str) -> bool:
    raw_lower = clause.lower()
    normalized = normalize_text_blob(clause)
    for alias in slug_aliases(slug):
        if "-" in alias:
            if alias in raw_lower:
                return True
        if f" {alias} " in normalized:
            return True
    return False


def derive_specificity(
    trigger_terms: frozenset[str],
    trigger_phrases: frozenset[str],
    description_brief: str,
    boundary_clauses: tuple[str, ...],
) -> str:
    score = 0
    if len(trigger_phrases) >= 4:
        score += 2
    elif len(trigger_phrases) >= 2:
        score += 1
    if len(trigger_terms) >= 18:
        score += 2
    elif len(trigger_terms) >= 10:
        score += 1
    lowered = description_brief.lower()
    if any(marker in lowered for marker in ("only use", "not for", "whenever", "specific", "explicitly")):
        score += 1
    if boundary_clauses:
        score += 1
    if score >= 5:
        return "narrow"
    if score >= 3:
        return "medium"
    return "broad"


def base_boundary_strength(row: SkillRow) -> float:
    strength = row.boundary_marker_count * 0.18
    if row.specificity_hint == "narrow":
        strength += 0.22
    elif row.specificity_hint == "medium":
        strength += 0.12
    if row.artifact_focus != "general":
        strength += 0.08
    if row.workflow_phase != "general":
        strength += 0.08
    if row.primary_intent != "general":
        strength += 0.05
    return min(strength, 1.0)


def build_skill_rows() -> list[SkillRow]:
    with BASE_CSV.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        base_rows: list[SkillRow] = []
        for row in reader:
            trigger_terms = parse_pipe_set(row["trigger_terms_extracted"])
            trigger_phrases = parse_pipe_set(row["trigger_phrases_raw"])
            boundary_clauses = collect_boundary_clauses(row["description_raw"])
            positive_description = strip_boundary_clauses(row["description_raw"])
            positive_trigger_phrases = tuple(
                phrase for phrase in trigger_phrases if not any(marker in phrase.lower() for marker in BOUNDARY_MARKERS)
            )
            text_blob = normalize_text_blob(
                row["skill_name"],
                row["skill_slug"],
                row["title"],
                row["description_brief"],
                positive_description,
                " | ".join(positive_trigger_phrases),
            )
            text_terms = tokenize_text(
                row["skill_name"],
                row["skill_slug"],
                row["title"],
                row["description_brief"],
                positive_description,
                " | ".join(positive_trigger_phrases),
            )
            brief_terms = tokenize_text(row["title"], row["description_brief"])
            family = classify_from_rules(text_terms, text_blob, FAMILY_RULES, "other")
            primary_intent = classify_from_rules(text_terms, text_blob, INTENT_RULES, "general")
            artifact_focus = classify_from_rules(text_terms, text_blob, ARTIFACT_RULES, "general")
            workflow_phase = classify_from_rules(text_terms, text_blob, PHASE_RULES, "general")
            specificity_hint = derive_specificity(
                trigger_terms=trigger_terms,
                trigger_phrases=trigger_phrases,
                description_brief=row["description_brief"],
                boundary_clauses=boundary_clauses,
            )
            base_rows.append(
                SkillRow(
                    row=row,
                    trigger_terms=trigger_terms,
                    trigger_phrases=trigger_phrases,
                    brief_terms=brief_terms,
                    text_terms=text_terms,
                    text_blob=text_blob,
                    family=family,
                    primary_intent=primary_intent,
                    artifact_focus=artifact_focus,
                    workflow_phase=workflow_phase,
                    specificity_hint=specificity_hint,
                    boundary_clauses=boundary_clauses,
                    boundary_marker_count=len(boundary_clauses),
                    explicit_boundary_targets=(),
                    explicit_prefer_targets=(),
                    boundary_strength=0.0,
                )
            )

    slugs = [row.row["skill_slug"] for row in base_rows]
    annotated_rows: list[SkillRow] = []
    for row in base_rows:
        boundary_targets: set[str] = set()
        prefer_targets: set[str] = set()
        for clause in row.boundary_clauses:
            for slug in slugs:
                if slug == row.row["skill_slug"]:
                    continue
                if clause_references_slug(clause, slug):
                    boundary_targets.add(slug)
                    if clause_has_redirect(clause):
                        prefer_targets.add(slug)
        updated = replace(
            row,
            explicit_boundary_targets=tuple(sorted(boundary_targets)),
            explicit_prefer_targets=tuple(sorted(prefer_targets)),
        )
        annotated_rows.append(replace(updated, boundary_strength=round(base_boundary_strength(updated) + min(0.12 * len(boundary_targets), 0.24), 3)))
    return annotated_rows


def jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    if not left or not right:
        return 0.0
    intersection = left & right
    union = left | right
    if not union:
        return 0.0
    return len(intersection) / len(union)


def directed_boundary_penalty(source: SkillRow, target: SkillRow) -> tuple[float, list[str]]:
    penalty = 0.0
    reasons: list[str] = []
    target_slug = target.row["skill_slug"]
    if target_slug in source.explicit_boundary_targets:
        penalty += 0.14
        reasons.append(f"{source.row['skill_slug']} explicitly fences to {target_slug}")
    if target_slug in source.explicit_prefer_targets:
        penalty += 0.08
        reasons.append(f"{source.row['skill_slug']} redirects to {target_slug}")
    return penalty, reasons


def specialization_penalty(left: SkillRow, right: SkillRow, family_match: bool, overlap_count: int) -> tuple[float, list[str]]:
    if not family_match and overlap_count < 2:
        return 0.0, []

    penalty = 0.0
    reasons: list[str] = []
    both_specific = left.specificity_hint != "broad" and right.specificity_hint != "broad"

    if left.artifact_focus != right.artifact_focus and left.artifact_focus != "general" and right.artifact_focus != "general":
        artifact_penalty = 0.09 if both_specific else 0.05
        penalty += artifact_penalty
        reasons.append("artifact specialization separates them")

    if left.workflow_phase != right.workflow_phase and left.workflow_phase != "general" and right.workflow_phase != "general":
        phase_penalty = 0.09 if both_specific or left.boundary_marker_count or right.boundary_marker_count else 0.05
        penalty += phase_penalty
        reasons.append("workflow phase specialization separates them")

    if left.primary_intent != right.primary_intent and left.primary_intent != "general" and right.primary_intent != "general":
        penalty += 0.04
        reasons.append("primary intent differs")

    return penalty, reasons


def collision_rationale(
    raw_score: float,
    final_score: float,
    family_match: bool,
    artifact_match: bool,
    phase_match: bool,
    overlap_count: int,
    boundary_penalty: float,
    boundary_reasons: list[str],
) -> str:
    parts: list[str] = []
    if family_match:
        parts.append("same family")
    if artifact_match:
        parts.append("same artifact focus")
    if phase_match:
        parts.append("same workflow phase")
    if overlap_count:
        parts.append(f"{overlap_count} shared trigger terms")
    parts.append(f"raw={raw_score:.2f}")
    if boundary_penalty > 0:
        parts.append(f"boundary_penalty={boundary_penalty:.2f}")
        parts.extend(boundary_reasons)
    parts.append(f"final={final_score:.2f}")
    return ", ".join(parts)


def score_collision(left: SkillRow, right: SkillRow) -> Collision | None:
    overlap_terms = tuple(sorted(left.trigger_terms & right.trigger_terms))
    overlap_count = len(overlap_terms)
    trigger_similarity = jaccard(left.trigger_terms, right.trigger_terms)
    text_similarity = jaccard(left.text_terms, right.text_terms)
    family_match = left.family == right.family and left.family != "other"
    artifact_match = left.artifact_focus == right.artifact_focus and left.artifact_focus != "general"
    phase_match = left.workflow_phase == right.workflow_phase and left.workflow_phase != "general"

    raw_score = trigger_similarity * 0.48 + text_similarity * 0.28
    if family_match:
        raw_score += 0.12
    if artifact_match:
        raw_score += 0.08
    if phase_match:
        raw_score += 0.05
    if overlap_count >= 6:
        raw_score += 0.10
    elif overlap_count >= 3:
        raw_score += 0.05

    left_penalty, left_reasons = directed_boundary_penalty(left, right)
    right_penalty, right_reasons = directed_boundary_penalty(right, left)
    specialization_delta, specialization_reasons = specialization_penalty(left, right, family_match, overlap_count)
    boundary_penalty = min(left_penalty + right_penalty + specialization_delta, 0.45)
    score = max(raw_score - boundary_penalty, 0.0)

    severity = ""
    # Thresholds calibrated 2026-03-15: MEDIUM raised from 0.28 to 0.35
    # Colisions < 0.35 are considered "expected noise" due to domain vocabulary
    HIGH_THRESHOLD = 0.44
    MEDIUM_THRESHOLD = 0.35
    LOW_THRESHOLD = 0.18

    if score >= HIGH_THRESHOLD and overlap_count >= 3 and family_match:
        severity = "high"
    elif score >= MEDIUM_THRESHOLD and (family_match or overlap_count >= 2):
        severity = "medium"
    elif score >= LOW_THRESHOLD and overlap_count >= 1:
        severity = "low"
    else:
        return None

    boundary_reasons = left_reasons + right_reasons + specialization_reasons
    return Collision(
        left=left.row["skill_slug"],
        right=right.row["skill_slug"],
        severity=severity,
        score=round(score, 4),
        raw_score=round(raw_score, 4),
        boundary_penalty=round(boundary_penalty, 4),
        family_match=family_match,
        artifact_match=artifact_match,
        phase_match=phase_match,
        overlap_count=overlap_count,
        overlap_terms=overlap_terms[:12],
        rationale=collision_rationale(
            raw_score=raw_score,
            final_score=score,
            family_match=family_match,
            artifact_match=artifact_match,
            phase_match=phase_match,
            overlap_count=overlap_count,
            boundary_penalty=boundary_penalty,
            boundary_reasons=boundary_reasons,
        ),
    )


def detect_collisions(rows: list[SkillRow]) -> list[Collision]:
    collisions: list[Collision] = []
    for left, right in itertools.combinations(rows, 2):
        collision = score_collision(left, right)
        if collision is not None:
            collisions.append(collision)
    collisions.sort(key=lambda item: ({"high": 0, "medium": 1, "low": 2}[item.severity], -item.score, item.left, item.right))
    return collisions


def write_enriched_csv(rows: list[SkillRow], collisions: list[Collision]) -> None:
    collision_counts: dict[str, int] = {}
    high_collision_counts: dict[str, int] = {}
    for collision in collisions:
        collision_counts[collision.left] = collision_counts.get(collision.left, 0) + 1
        collision_counts[collision.right] = collision_counts.get(collision.right, 0) + 1
        if collision.severity == "high":
            high_collision_counts[collision.left] = high_collision_counts.get(collision.left, 0) + 1
            high_collision_counts[collision.right] = high_collision_counts.get(collision.right, 0) + 1

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = list(rows[0].row.keys()) + [
            "family",
            "primary_intent",
            "artifact_focus",
            "workflow_phase",
            "specificity_hint",
            "boundary_marker_count",
            "explicit_boundary_targets",
            "explicit_prefer_targets",
            "boundary_strength",
            "has_raw_trigger_phrases",
            "has_extracted_trigger_terms",
            "collision_partner_count",
            "high_collision_count",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in rows:
            row = dict(item.row)
            row.update(
                {
                    "family": item.family,
                    "primary_intent": item.primary_intent,
                    "artifact_focus": item.artifact_focus,
                    "workflow_phase": item.workflow_phase,
                    "specificity_hint": item.specificity_hint,
                    "boundary_marker_count": item.boundary_marker_count,
                    "explicit_boundary_targets": " | ".join(item.explicit_boundary_targets),
                    "explicit_prefer_targets": " | ".join(item.explicit_prefer_targets),
                    "boundary_strength": f"{item.boundary_strength:.2f}",
                    "has_raw_trigger_phrases": str(bool(item.trigger_phrases)).lower(),
                    "has_extracted_trigger_terms": str(bool(item.trigger_terms)).lower(),
                    "collision_partner_count": collision_counts.get(item.row["skill_slug"], 0),
                    "high_collision_count": high_collision_counts.get(item.row["skill_slug"], 0),
                }
            )
            writer.writerow(row)


def lot_collision_summary(lot_skills: tuple[str, ...], collisions: list[Collision]) -> tuple[int, int]:
    all_count = 0
    high_count = 0
    relevant = set(lot_skills)
    for collision in collisions:
        if collision.left in relevant and collision.right in relevant:
            all_count += 1
            if collision.severity == "high":
                high_count += 1
    return all_count, high_count


def top_collisions_by_lot(lot_skills: tuple[str, ...], collisions: list[Collision], limit: int = 5) -> list[Collision]:
    relevant = set(lot_skills)
    return [collision for collision in collisions if collision.left in relevant and collision.right in relevant][:limit]


def family_counts(rows: list[SkillRow]) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.family] = counts.get(row.family, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def severity_counts(collisions: list[Collision]) -> dict[str, int]:
    counts = {"high": 0, "medium": 0, "low": 0}
    for collision in collisions:
        counts[collision.severity] += 1
    return counts


def format_collision(collision: Collision) -> str:
    overlap = ", ".join(collision.overlap_terms[:6]) if collision.overlap_terms else "n/a"
    return (
        f"- `{collision.left}` vs `{collision.right}` — severity={collision.severity}, "
        f"score={collision.score:.2f}, raw={collision.raw_score:.2f}, penalty={collision.boundary_penalty:.2f}, overlap={overlap}"
    )


def write_report(rows: list[SkillRow], collisions: list[Collision]) -> None:
    counts = severity_counts(collisions)
    top_collisions = collisions[:20]
    families = family_counts(rows)

    lines: list[str] = []
    lines.append("# Skills Trigger Collision Report")
    lines.append("")
    lines.append("## Executive summary")
    lines.append("")
    lines.append(f"- Skills analyzed: {len(rows)}")
    lines.append(f"- Collision candidates: {len(collisions)}")
    lines.append(f"- High severity: {counts['high']}")
    lines.append(f"- Medium severity: {counts['medium']}")
    lines.append(f"- Low severity: {counts['low']}")
    lines.append("")
    lines.append("## Threshold calibration")
    lines.append("")
    lines.append("| Severity | Threshold | Description |")
    lines.append("|----------|-----------|-------------|")
    lines.append("| HIGH     | >= 0.44   | Intervention required |")
    lines.append("| MEDIUM   | >= 0.35   | Review recommended |")
    lines.append("| LOW      | >= 0.18   | Expected noise, acceptable |")
    lines.append("")
    lines.append("**Note:** Collisions with MEDIUM score < 0.40 are generally unavoidable when skills share domain vocabulary (e.g., 'claude', 'code', 'sessions' in AI-related skills).")
    lines.append("")
    lines.append("## Family distribution")
    lines.append("")
    for family, count in families:
        lines.append(f"- `{family}`: {count}")
    lines.append("")
    lines.append("## Top collision candidates")
    lines.append("")
    for collision in top_collisions:
        lines.append(format_collision(collision))
        lines.append(f"  - rationale: {collision.rationale}")
    lines.append("")
    lines.append("## Prioritized intervention backlog")
    lines.append("")
    for lot_name, lot_skills, reason in PRIORITY_LOTS:
        total, high = lot_collision_summary(lot_skills, collisions)
        lines.append(f"### {lot_name}")
        lines.append("")
        lines.append(f"- skills: {', '.join(f'`{skill}`' for skill in lot_skills)}")
        lines.append(f"- why now: {reason}")
        lines.append(f"- collisions in lot: {total}")
        lines.append(f"- high severity in lot: {high}")
        top_in_lot = top_collisions_by_lot(lot_skills, collisions)
        if top_in_lot:
            lines.append("- top cases:")
            for collision in top_in_lot:
                lines.append(f"  {format_collision(collision)[2:]}")
        else:
            lines.append("- top cases: none detected by current heuristic")
        lines.append("")
    lines.append("## Heuristic notes")
    lines.append("")
    lines.append("- Collision score is now boundary-aware: raw lexical overlap is reduced by explicit fences such as `Do NOT use`, `Prefer this over`, artifact specialization, and workflow-phase specialization.")
    lines.append("- `boundary_strength` in the enriched CSV is a per-skill hint for how strongly that skill declares its own frontier.")
    lines.append("- This report is for prioritization only; it does not modify any `SKILL.md` file.")
    lines.append("- False positives remain possible, especially for broad generic skills or skills that mention siblings without an explicit fence.")

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_skill_rows()
    collisions = detect_collisions(rows)
    write_enriched_csv(rows, collisions)
    write_report(rows, collisions)
    counts = severity_counts(collisions)
    print(f"skills={len(rows)}")
    print(f"collisions={len(collisions)}")
    print(f"high={counts['high']}")
    print(f"medium={counts['medium']}")
    print(f"low={counts['low']}")
    print(f"enriched_csv={OUT_CSV}")
    print(f"report={OUT_REPORT}")


if __name__ == "__main__":
    main()
