"""Regression tests for query expansion with generated aliases.

These tests validate that the keyword extraction and alias generation
improves (or at least doesn't degrade) query expansion results.

Benchmark queries are based on common use cases from the plan.
"""

from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]

from src.application.keyword_extractor import KeywordExtractor
from src.infrastructure.aliases_fs import merge_aliases


# Benchmark queries from the plan
BENCHMARK_QUERIES = [
    "pytest",
    "security",
    "sqlite",
    "clean architecture",
    "code review",
    "performance",
    "debug python",
    "tdd",
    "testing",
    "database",
]


class MockSkillSet:
    """Mock skill set for regression testing."""

    @staticmethod
    def get_sample_skills() -> list[dict[str, str]]:
        """Get a representative sample of skills for testing.

        These simulate the types of skills found in the skills-hub.
        """
        return [
            {
                "name": "tdd-workflow",
                "source_path": "/skills/tdd-workflow/SKILL.md",
                "description": "Test-driven development workflow with pytest and coverage requirements",
            },
            {
                "name": "python-testing",
                "source_path": "/skills/python-testing/SKILL.md",
                "description": "Python testing strategies using pytest, fixtures, mocking",
            },
            {
                "name": "security-review",
                "source_path": "/skills/security-review/SKILL.md",
                "description": "Security vulnerability detection and code review for authentication",
            },
            {
                "name": "sqlite-query-plans",
                "source_path": "/skills/sqlite-query-plans/SKILL.md",
                "description": "SQLite query optimization and indexing strategies",
            },
            {
                "name": "clean-architecture",
                "source_path": "/skills/clean-architecture/SKILL.md",
                "description": "Clean architecture patterns for layered application design",
            },
            {
                "name": "code-review-checklist",
                "source_path": "/skills/code-review-checklist/SKILL.md",
                "description": "Code review patterns and best practices for quality",
            },
            {
                "name": "performance-optimization",
                "source_path": "/skills/performance-optimization/SKILL.md",
                "description": "Performance profiling and optimization techniques",
            },
            {
                "name": "python-debugging",
                "source_path": "/skills/python-debugging/SKILL.md",
                "description": "Debug Python applications with logging and tracing",
            },
            {
                "name": "postgres-patterns",
                "source_path": "/skills/postgres-patterns/SKILL.md",
                "description": "PostgreSQL database patterns for query optimization",
            },
            {
                "name": "django-security",
                "source_path": "/skills/django-security/SKILL.md",
                "description": "Django security best practices for web applications",
            },
            {
                "name": "api-security-hardening",
                "source_path": "/skills/api-security-hardening/SKILL.md",
                "description": "Secure HTTP APIs with authentication and rate limiting",
            },
            {
                "name": "django-testing",
                "source_path": "/skills/django-testing/SKILL.md",
                "description": "Django testing strategies with pytest integration",
            },
        ]


class TestQueryExpansionSmoke:
    """Smoke tests for query expansion with generated aliases."""

    @pytest.fixture
    def extractor(self) -> KeywordExtractor:
        """Create a KeywordExtractor with default settings."""
        return KeywordExtractor(min_frequency=1)  # Use min_frequency=1 for small sample

    @pytest.fixture
    def generated_aliases(self, extractor: KeywordExtractor) -> dict[str, list[str]]:
        """Generate aliases from sample skills."""
        skills = MockSkillSet.get_sample_skills()
        extracted = extractor.extract_from_skills(skills)
        alias_map = extractor.build_alias_map(extracted)
        return alias_map.aliases

    def test_pytest_query_finds_testing_skills(
        self, generated_aliases: dict[str, list[str]]
    ) -> None:
        """Query 'pytest' should find testing-related skills."""
        # Check if pytest-related aliases exist
        pytest_found = False
        testing_found = False

        for alias, skills in generated_aliases.items():
            if "pytest" in alias.lower():
                pytest_found = True
            if "testing" in alias.lower():
                testing_found = True

        # At minimum, pytest should be extracted from skill names/descriptions
        # or testing should be captured
        assert pytest_found or testing_found, (
            f"Expected 'pytest' or 'testing' in aliases. "
            f"Got: {list(generated_aliases.keys())[:10]}..."
        )

    def test_security_query_finds_security_skills(
        self, generated_aliases: dict[str, list[str]]
    ) -> None:
        """Query 'security' should find security-related skills."""
        security_aliases = [
            alias for alias in generated_aliases.keys() if "security" in alias.lower()
        ]

        assert len(security_aliases) > 0, (
            f"Expected 'security' related aliases. Got: {list(generated_aliases.keys())[:10]}..."
        )

    def test_sqlite_query_finds_sqlite_skills(
        self, generated_aliases: dict[str, list[str]]
    ) -> None:
        """Query 'sqlite' should find sqlite-related skills."""
        sqlite_aliases = [alias for alias in generated_aliases.keys() if "sqlite" in alias.lower()]

        assert len(sqlite_aliases) > 0, (
            f"Expected 'sqlite' related aliases. Got: {list(generated_aliases.keys())[:10]}..."
        )

    def test_clean_architecture_query(self, generated_aliases: dict[str, list[str]]) -> None:
        """Query 'clean architecture' should find architecture skills."""
        arch_aliases = [
            alias
            for alias in generated_aliases.keys()
            if "architecture" in alias.lower() or "clean" in alias.lower()
        ]

        assert len(arch_aliases) > 0, (
            f"Expected architecture related aliases. Got: {list(generated_aliases.keys())[:10]}..."
        )

    def test_code_review_query(self, generated_aliases: dict[str, list[str]]) -> None:
        """Query 'code review' should find review skills."""
        review_aliases = [
            alias
            for alias in generated_aliases.keys()
            if "review" in alias.lower() or "code" in alias.lower()
        ]

        assert len(review_aliases) > 0, (
            f"Expected review related aliases. Got: {list(generated_aliases.keys())[:10]}..."
        )

    def test_performance_query(self, generated_aliases: dict[str, list[str]]) -> None:
        """Query 'performance' should find performance skills."""
        perf_aliases = [
            alias
            for alias in generated_aliases.keys()
            if "performance" in alias.lower() or "optimization" in alias.lower()
        ]

        assert len(perf_aliases) > 0, (
            f"Expected performance related aliases. Got: {list(generated_aliases.keys())[:10]}..."
        )

    def test_debug_python_query(self, generated_aliases: dict[str, list[str]]) -> None:
        """Query 'debug python' should find debugging skills."""
        debug_aliases = [
            alias
            for alias in generated_aliases.keys()
            if "debug" in alias.lower() or "debugging" in alias.lower()
        ]

        assert len(debug_aliases) > 0, (
            f"Expected debug related aliases. Got: {list(generated_aliases.keys())[:10]}..."
        )

    def test_no_generic_aliases_generated(self, generated_aliases: dict[str, list[str]]) -> None:
        """No generic/useless aliases should be generated."""
        # These are examples of overly generic terms that should NOT appear
        banned_terms = {"use", "using", "when", "help", "task", "user"}

        for banned in banned_terms:
            assert banned not in generated_aliases, (
                f"Generic term '{banned}' should not be in aliases"
            )

    def test_aliases_are_lowercase(self, generated_aliases: dict[str, list[str]]) -> None:
        """All alias keys should be lowercase."""
        for alias in generated_aliases.keys():
            assert alias == alias.lower(), f"Alias '{alias}' should be lowercase"

    def test_aliases_have_valid_structure(self, generated_aliases: dict[str, list[str]]) -> None:
        """All aliases should have valid structure."""
        for alias, skills in generated_aliases.items():
            assert isinstance(alias, str), f"Alias key should be string: {alias}"
            assert isinstance(skills, list), f"Skills should be list for: {alias}"
            for skill in skills:
                assert isinstance(skill, str), f"Skill should be string: {skill}"

    def test_manual_and_generated_merge_correctly(self) -> None:
        """Manual and generated aliases should merge correctly."""
        manual = {
            "testing": ["manual-test-skill"],
            "review": ["manual-review-skill"],
        }
        generated = {
            "testing": ["generated-test-skill"],
            "database": ["generated-db-skill"],
        }

        merged = merge_aliases(manual, generated)

        # Manual takes precedence
        assert merged["testing"] == ["manual-test-skill"]
        # Generated adds new keys
        assert "database" in merged
        assert merged["database"] == ["generated-db-skill"]
        # Generated doesn't override manual
        assert "review" in merged
        assert merged["review"] == ["manual-review-skill"]

    def test_deterministic_alias_generation(self) -> None:
        """Alias generation should be deterministic."""
        extractor = KeywordExtractor(min_frequency=1)
        skills = MockSkillSet.get_sample_skills()

        # Generate twice
        extracted1 = extractor.extract_from_skills(skills)
        alias_map1 = extractor.build_alias_map(extracted1)

        extracted2 = extractor.extract_from_skills(skills)
        alias_map2 = extractor.build_alias_map(extracted2)

        # Should be identical
        assert alias_map1.aliases == alias_map2.aliases

    def test_yaml_output_is_valid(
        self, generated_aliases: dict[str, list[str]], tmp_path: Path
    ) -> None:
        """Generated YAML should be valid and readable."""
        output_path = tmp_path / "test_aliases.yaml"

        # Write YAML
        data = {"schema_version": 1, "aliases": generated_aliases}
        with open(output_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=True)

        # Read back
        with open(output_path, "r") as f:
            loaded = yaml.safe_load(f)

        assert loaded["schema_version"] == 1
        assert loaded["aliases"] == generated_aliases


class TestBenchmarkQueriesCoverage:
    """Test coverage of benchmark queries."""

    def test_all_benchmark_queries_covered(self) -> None:
        """Each benchmark query should have potential alias coverage."""
        extractor = KeywordExtractor(min_frequency=1)
        skills = MockSkillSet.get_sample_skills()
        extracted = extractor.extract_from_skills(skills)
        alias_map = extractor.build_alias_map(extracted)
        all_aliases = set(alias_map.aliases.keys())

        # For each benchmark query, check if there's at least partial coverage
        coverage_report: dict[str, list[str]] = {}

        for query in BENCHMARK_QUERIES:
            query_terms = query.lower().split()
            matching_aliases = [
                alias for alias in all_aliases if any(term in alias for term in query_terms)
            ]
            coverage_report[query] = matching_aliases

        # At least 50% of benchmark queries should have coverage
        covered = sum(1 for matches in coverage_report.values() if matches)
        coverage_rate = covered / len(BENCHMARK_QUERIES)

        assert coverage_rate >= 0.5, (
            f"Expected at least 50% benchmark coverage, got {coverage_rate:.0%}. "
            f"Coverage: {coverage_report}"
        )
