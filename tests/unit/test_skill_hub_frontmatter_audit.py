from __future__ import annotations

from src.domain.skill_hub_frontmatter_audit import (
    FrontmatterAuditTarget,
    audit_frontmatter_targets,
    inspect_frontmatter,
)


def _target(content: str, *, name: str = "demo-skill", source: str = "demo") -> FrontmatterAuditTarget:
    return FrontmatterAuditTarget(
        source=source,
        name=name,
        source_path=f"/tmp/{name}/SKILL.md",
        content=content,
    )


def test_inspect_frontmatter_accepts_valid_yaml_mapping() -> None:
    target = _target(
        "---\nname: demo-skill\ndescription: \"Valid description: with colon\"\n---\n\n# Demo\n"
    )

    result = inspect_frontmatter(target)

    assert result is None


def test_inspect_frontmatter_reports_missing_frontmatter() -> None:
    target = _target("# Demo without frontmatter\n")

    result = inspect_frontmatter(target)

    assert result is not None
    assert result.error_family == "missing_frontmatter"
    assert result.error_type == "MissingFrontmatter"


def test_inspect_frontmatter_reports_unterminated_block() -> None:
    target = _target("---\nname: broken\n")

    result = inspect_frontmatter(target)

    assert result is not None
    assert result.error_family == "unterminated_frontmatter"
    assert result.error_type == "UnterminatedFrontmatter"


def test_inspect_frontmatter_classifies_scanner_error() -> None:
    target = _target(
        "---\nname: demo-skill\ndescription: Use when testing. Triggers on: invalid colon usage.\n---\n"
    )

    result = inspect_frontmatter(target)

    assert result is not None
    assert result.error_family == "yaml_parse_error"
    assert result.error_type == "ScannerError"


def test_inspect_frontmatter_classifies_parser_error() -> None:
    target = _target(
        "---\nname: demo-skill\ndescription: \"Use when user says \"hello\"\"\n---\n"
    )

    result = inspect_frontmatter(target)

    assert result is not None
    assert result.error_family == "yaml_parse_error"
    assert result.error_type == "ParserError"


def test_audit_frontmatter_targets_counts_failures_by_error_type() -> None:
    report = audit_frontmatter_targets(
        [
            _target("---\nname: ok\ndescription: ok\n---\n", name="ok"),
            _target(
                "---\nname: bad-scan\ndescription: Use when invalid. Triggers on: colon.\n---\n",
                name="bad-scan",
            ),
            _target(
                "---\nname: bad-parse\ndescription: \"nested \"quote\" problem\"\n---\n",
                name="bad-parse",
            ),
        ]
    )

    assert report.total_targets == 3
    assert report.broken_count == 2
    assert report.count_by_error_type() == {"ScannerError": 1, "ParserError": 1}
