from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "analyze_skills_catalog.py"
SPEC = importlib.util.spec_from_file_location("analyze_skills_catalog", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
analyzer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = analyzer
SPEC.loader.exec_module(analyzer)


def make_skill(
    *,
    slug: str,
    description_raw: str,
    description_brief: str,
    trigger_terms: set[str],
    trigger_phrases: set[str],
    family: str,
    intent: str,
    artifact: str,
    phase: str,
    specificity: str = "narrow",
    boundary_targets: tuple[str, ...] = (),
    prefer_targets: tuple[str, ...] = (),
) -> analyzer.SkillRow:
    row = {
        "skill_name": slug,
        "skill_slug": slug,
        "source_group": "test",
        "path": f"/tmp/{slug}/SKILL.md",
        "title": slug,
        "description_raw": description_raw,
        "description_brief": description_brief,
        "trigger_phrases_raw": " | ".join(sorted(trigger_phrases)),
        "trigger_terms_extracted": " | ".join(sorted(trigger_terms)),
        "trigger_count": str(len(trigger_terms | trigger_phrases)),
    }
    return analyzer.SkillRow(
        row=row,
        trigger_terms=frozenset(trigger_terms),
        trigger_phrases=frozenset(trigger_phrases),
        brief_terms=analyzer.tokenize_text(slug, description_brief),
        text_terms=analyzer.tokenize_text(
            slug,
            description_raw,
            description_brief,
            row["trigger_terms_extracted"],
            row["trigger_phrases_raw"],
        ),
        text_blob=analyzer.normalize_text_blob(
            slug,
            description_raw,
            description_brief,
            row["trigger_terms_extracted"],
            row["trigger_phrases_raw"],
        ),
        family=family,
        primary_intent=intent,
        artifact_focus=artifact,
        workflow_phase=phase,
        specificity_hint=specificity,
        boundary_clauses=analyzer.collect_boundary_clauses(description_raw),
        boundary_marker_count=len(analyzer.collect_boundary_clauses(description_raw)),
        explicit_boundary_targets=boundary_targets,
        explicit_prefer_targets=prefer_targets,
        boundary_strength=0.75,
    )


def test_phase_classifier_prefers_verification_for_verification_loop_text() -> None:
    description = (
        "Run a comprehensive quality verification loop (build, typecheck, lint, tests, security scan, diff review) "
        "before creating a PR or after significant changes. Use when completing a feature, refactoring, or ensuring all quality gates pass."
    )
    text_terms = analyzer.tokenize_text("verification-loop", description)
    text_blob = analyzer.normalize_text_blob("verification-loop", description)

    phase = analyzer.classify_from_rules(text_terms, text_blob, analyzer.PHASE_RULES, "general")

    assert phase == "verification"


def test_explicit_boundary_penalty_demotes_cli_vs_rctl_collision() -> None:
    cli = make_skill(
        slug="cli-explorer",
        description_raw=(
            'Quick repo search. Do NOT use for reviewctl workflows (use rctl-explore instead) or for broad system explanation (use codebase-explorer).'
        ),
        description_brief="Fast terminal-first repo search.",
        trigger_terms={"search", "repo", "reviewctl", "explore", "grep", "files", "codebase", "analysis", "workflow", "structured", "output"},
        trigger_phrases={"grep for", "search for pattern", "structured search"},
        family="search-exploration-retrieval",
        intent="search",
        artifact="code",
        phase="discovery",
        boundary_targets=("codebase-explorer", "rctl-explore"),
        prefer_targets=("codebase-explorer", "rctl-explore"),
    )
    rctl = make_skill(
        slug="rctl-explore",
        description_raw=(
            'Structured reviewctl exploration. ONLY use when running reviewctl explore context or diff. '
            'NOT for ad-hoc repo searches (use cli-explorer instead).'
        ),
        description_brief="Reviewctl exploration flow.",
        trigger_terms={"search", "repo", "reviewctl", "explore", "context", "diff", "artifacts", "analysis", "workflow", "structured", "output"},
        trigger_phrases={"reviewctl explore context", "reviewctl explore diff", "structured analysis"},
        family="search-exploration-retrieval",
        intent="operate",
        artifact="code",
        phase="discovery",
        boundary_targets=("cli-explorer",),
        prefer_targets=("cli-explorer",),
    )

    left_penalty, left_reasons = analyzer.directed_boundary_penalty(cli, rctl)
    right_penalty, right_reasons = analyzer.directed_boundary_penalty(rctl, cli)
    collision = analyzer.score_collision(cli, rctl)

    assert left_penalty > 0
    assert right_penalty > 0
    assert left_reasons or right_reasons
    if collision is not None:
        assert collision.boundary_penalty >= 0.30
        assert collision.raw_score > collision.score
        assert collision.severity != "high"
        assert "explicitly fences" in collision.rationale or "redirects" in collision.rationale


def test_artifact_and_phase_specialization_reduce_borderline_overlap() -> None:
    doc_lookup = make_skill(
        slug="context7-docs",
        description_raw="Search current library docs. Only use for programming library documentation and migration guidance.",
        description_brief="Programming library docs lookup.",
        trigger_terms={"search", "docs", "documentation", "libraries", "frameworks", "api", "content", "page", "lookup", "current"},
        trigger_phrases={"current docs", "api references", "documentation lookup"},
        family="search-exploration-retrieval",
        intent="search",
        artifact="code",
        phase="discovery",
    )
    url_reader = make_skill(
        slug="web-fetch",
        description_raw="Fetch a specific URL. Use when the user already has a page URL and wants readable content.",
        description_brief="Specific URL reader.",
        trigger_terms={"search", "docs", "url", "page", "content", "fetch", "documentation", "lookup", "current", "api"},
        trigger_phrases={"specific URL", "read this page", "documentation page"},
        family="search-exploration-retrieval",
        intent="search",
        artifact="browser-web",
        phase="implementation",
        specificity="medium",
    )

    collision = analyzer.score_collision(doc_lookup, url_reader)

    assert collision is not None
    assert collision.boundary_penalty >= 0.14
    assert collision.raw_score > collision.score
    assert "artifact specialization separates them" in collision.rationale
    assert "workflow phase specialization separates them" in collision.rationale
