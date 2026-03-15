"""Tests for keyword extraction from skill metadata.

TDD RED phase - these tests define the expected behavior for extracting
keywords from skill names and descriptions for alias generation.
"""

from dataclasses import FrozenInstanceError

import pytest

from src.application.keyword_extractor import (
    BLACKLIST,
    SHORT_TOKEN_WHITELIST,
    STOPWORDS_EN,
    STOPWORDS_ES,
    ExtractedSkillKeywords,
    GeneratedAliasMap,
    KeywordExtractor,
    extract_name_tokens,
    normalize_token,
    tokenize_description,
)


class TestExtractNameTokens:
    """Tests for token extraction from skill names."""

    def test_kebab_case_splitting(self) -> None:
        """kebab-case names should be split into tokens."""
        tokens = extract_name_tokens("tdd-workflow")
        assert tokens == frozenset({"tdd", "workflow"})

    def test_snake_case_splitting(self) -> None:
        """snake_case names should be split into tokens."""
        tokens = extract_name_tokens("sqlite_query_plans")
        assert tokens == frozenset({"sqlite", "query", "plans"})

    def test_camel_case_splitting(self) -> None:
        """camelCase names should be split into tokens."""
        tokens = extract_name_tokens("codeReview")
        assert tokens == frozenset({"code", "review"})

    def test_pascal_case_splitting(self) -> None:
        """PascalCase names should be split into tokens."""
        tokens = extract_name_tokens("CodeReviewHelper")
        assert tokens == frozenset({"code", "review", "helper"})

    def test_mixed_case_splitting(self) -> None:
        """Mixed kebab-camelCase should be split correctly."""
        tokens = extract_name_tokens("api-client-handler")
        assert tokens == frozenset({"api", "client", "handler"})

    def test_lowercase_normalization(self) -> None:
        """All tokens should be lowercase."""
        tokens = extract_name_tokens("TDD-Workflow")
        assert "tdd" in tokens
        assert "workflow" in tokens
        assert "TDD" not in tokens
        assert "Workflow" not in tokens

    def test_empty_name_returns_empty(self) -> None:
        """Empty name should return empty frozenset."""
        tokens = extract_name_tokens("")
        assert tokens == frozenset()

    def test_single_word_name(self) -> None:
        """Single word name should return single token."""
        tokens = extract_name_tokens("pytest")
        assert tokens == frozenset({"pytest"})


class TestNormalizeToken:
    """Tests for token normalization and filtering."""

    def test_lowercase_conversion(self) -> None:
        """Token should be converted to lowercase."""
        result = normalize_token("UPPERCASE")
        assert result == "uppercase"

    def test_trim_whitespace(self) -> None:
        """Token should have whitespace trimmed."""
        result = normalize_token("  token  ")
        assert result == "token"

    def test_remove_peripheral_punctuation(self) -> None:
        """Peripheral punctuation should be removed."""
        result = normalize_token('"token"')
        assert result == "token"

    def test_filter_stopword_english(self) -> None:
        """English stopwords should return None."""
        assert normalize_token("the") is None
        assert normalize_token("and") is None
        assert normalize_token("for") is None
        assert normalize_token("with") is None

    def test_filter_stopword_spanish(self) -> None:
        """Spanish stopwords should return None."""
        assert normalize_token("para") is None
        assert normalize_token("cuando") is None
        assert normalize_token("usar") is None

    def test_filter_short_tokens(self) -> None:
        """Tokens shorter than 3 chars should return None (unless whitelisted)."""
        assert normalize_token("ab") is None
        assert normalize_token("a") is None

    def test_whitelist_short_tokens(self) -> None:
        """Whitelisted short tokens should pass through."""
        assert normalize_token("tdd") == "tdd"
        assert normalize_token("sql") == "sql"
        assert normalize_token("api") == "api"
        assert normalize_token("cli") == "cli"
        assert normalize_token("ui") == "ui"
        assert normalize_token("fp") == "fp"

    def test_blacklist_generic_tokens(self) -> None:
        """Blacklisted generic tokens should return None."""
        assert normalize_token("use") is None
        assert normalize_token("using") is None
        assert normalize_token("when") is None
        assert normalize_token("help") is None
        assert normalize_token("task") is None
        assert normalize_token("user") is None

    def test_valid_token_passes_through(self) -> None:
        """Valid token should pass through normalized."""
        assert normalize_token("Database") == "database"
        assert normalize_token("  Testing  ") == "testing"


class TestTokenizeDescription:
    """Tests for tokenization of skill descriptions."""

    def test_basic_tokenization(self) -> None:
        """Description should be split into tokens."""
        tokens = tokenize_description("Python testing strategies using pytest")
        assert "python" in tokens
        assert "testing" in tokens
        assert "strategies" in tokens
        assert "pytest" in tokens

    def test_stopwords_filtered(self) -> None:
        """Stopwords should be filtered from description."""
        tokens = tokenize_description("Use this for testing with pytest")
        assert "use" not in tokens
        assert "this" not in tokens
        assert "for" not in tokens
        assert "with" not in tokens
        assert "testing" in tokens
        assert "pytest" in tokens

    def test_deduplication(self) -> None:
        """Duplicate tokens should be deduplicated."""
        tokens = tokenize_description("testing testing testing pytest pytest")
        assert tokens.count("testing") == 1
        assert tokens.count("pytest") == 1

    def test_empty_description_returns_empty(self) -> None:
        """Empty description should return empty list."""
        tokens = tokenize_description("")
        assert tokens == []

    def test_only_stopwords_returns_empty(self) -> None:
        """Description with only stopwords should return empty list."""
        tokens = tokenize_description("the and for with use when")
        assert tokens == []

    def test_punctuation_handling(self) -> None:
        """Punctuation should be handled gracefully."""
        tokens = tokenize_description("Testing, debugging, and profiling!")
        assert "testing" in tokens
        assert "debugging" in tokens
        assert "profiling" in tokens
        assert "and" not in tokens  # stopword


class TestExtractedSkillKeywords:
    """Tests for ExtractedSkillKeywords dataclass."""

    def test_frozen_dataclass(self) -> None:
        """ExtractedSkillKeywords should be immutable."""
        skill_kw = ExtractedSkillKeywords(
            skill_name="tdd-workflow",
            source_path="/path/to/skill.md",
            keywords=frozenset({"tdd", "workflow"}),
        )
        with pytest.raises(FrozenInstanceError):
            skill_kw.skill_name = "modified"  # type: ignore[misc]

    def test_keywords_is_frozenset(self) -> None:
        """keywords field should be a frozenset."""
        skill_kw = ExtractedSkillKeywords(
            skill_name="test",
            source_path="/path",
            keywords=frozenset({"a", "b"}),
        )
        assert isinstance(skill_kw.keywords, frozenset)


class TestGeneratedAliasMap:
    """Tests for GeneratedAliasMap dataclass."""

    def test_frozen_dataclass(self) -> None:
        """GeneratedAliasMap should be immutable."""
        alias_map = GeneratedAliasMap(
            schema_version=1,
            aliases={"test": ["skill1", "skill2"]},
        )
        with pytest.raises(FrozenInstanceError):
            alias_map.schema_version = 2  # type: ignore[misc]

    def test_default_schema_version(self) -> None:
        """schema_version should default to 1."""
        alias_map = GeneratedAliasMap(aliases={})
        assert alias_map.schema_version == 1


class TestKeywordExtractor:
    """Tests for KeywordExtractor class."""

    @pytest.fixture
    def extractor(self) -> KeywordExtractor:
        """Create a KeywordExtractor with default settings."""
        return KeywordExtractor()

    @pytest.fixture
    def sample_skills(self) -> list[dict[str, str]]:
        """Sample skill metadata for testing."""
        return [
            {
                "name": "tdd-workflow",
                "source_path": "/path/to/tdd-workflow/SKILL.md",
                "description": "Test-driven development workflow with pytest",
            },
            {
                "name": "code-review",
                "source_path": "/path/to/code-review/SKILL.md",
                "description": "Code review patterns and best practices",
            },
            {
                "name": "sqlite-query-plans",
                "source_path": "/path/to/sqlite-query-plans/SKILL.md",
                "description": "SQLite query optimization and indexing strategies",
            },
        ]

    def test_extract_from_single_skill(self, extractor: KeywordExtractor) -> None:
        """Should extract keywords from a single skill."""
        skill = {
            "name": "tdd-workflow",
            "source_path": "/path/to/skill.md",
            "description": "Test-driven development workflow",
        }
        result = extractor.extract_from_skill(skill)
        assert result is not None
        assert result.skill_name == "tdd-workflow"
        assert "tdd" in result.keywords
        assert "workflow" in result.keywords
        assert "test" in result.keywords  # from description
        assert "driven" in result.keywords  # from description

    def test_extract_from_skills_batch(
        self, extractor: KeywordExtractor, sample_skills: list[dict[str, str]]
    ) -> None:
        """Should extract keywords from multiple skills."""
        results = extractor.extract_from_skills(sample_skills)
        assert len(results) == 3
        names = [r.skill_name for r in results]
        assert "tdd-workflow" in names
        assert "code-review" in names
        assert "sqlite-query-plans" in names

    def test_build_alias_map_min_frequency(self, extractor: KeywordExtractor) -> None:
        """Should enforce min_frequency=2 default."""
        # Two skills with 'testing' keyword
        skills = [
            {
                "name": "pytest-testing",
                "source_path": "/a.md",
                "description": "Testing with pytest",
            },
            {
                "name": "unittest-testing",
                "source_path": "/b.md",
                "description": "Testing with unittest",
            },
            {
                "name": "single-occurrence",
                "source_path": "/c.md",
                "description": "Unique keyword xyzabc",
            },
        ]
        extracted = extractor.extract_from_skills(skills)
        alias_map = extractor.build_alias_map(extracted)

        # 'testing' appears in both skills -> should be in alias map
        assert "testing" in alias_map.aliases
        # 'xyzabc' only appears once -> should NOT be in alias map
        assert "xyzabc" not in alias_map.aliases

    def test_build_alias_map_max_skills_per_alias(self, extractor: KeywordExtractor) -> None:
        """Should enforce max_skills_per_alias=8 default."""
        # Create 10 skills all sharing 'database' keyword
        skills = [
            {
                "name": f"database-skill-{i}",
                "source_path": f"/{i}.md",
                "description": "Database operations",
            }
            for i in range(10)
        ]
        extracted = extractor.extract_from_skills(skills)
        alias_map = extractor.build_alias_map(extracted)

        # 'database' should be in the map but capped at 8 skills
        if "database" in alias_map.aliases:
            assert len(alias_map.aliases["database"]) <= 8

    def test_deterministic_output(
        self, extractor: KeywordExtractor, sample_skills: list[dict[str, str]]
    ) -> None:
        """Output should be deterministic (same input -> same output)."""
        extracted1 = extractor.extract_from_skills(sample_skills)
        alias_map1 = extractor.build_alias_map(extracted1)

        extracted2 = extractor.extract_from_skills(sample_skills)
        alias_map2 = extractor.build_alias_map(extracted2)

        assert alias_map1.aliases == alias_map2.aliases

    def test_alias_ordering_deterministic(self, extractor: KeywordExtractor) -> None:
        """Alias skill lists should be ordered deterministically."""
        skills = [
            {"name": "zebra-skill", "source_path": "/z.md", "description": "testing"},
            {"name": "alpha-skill", "source_path": "/a.md", "description": "testing"},
            {"name": "middle-skill", "source_path": "/m.md", "description": "testing"},
        ]
        extracted = extractor.extract_from_skills(skills)
        alias_map = extractor.build_alias_map(extracted)

        if "testing" in alias_map.aliases:
            # Should be alphabetically sorted
            skills_list = alias_map.aliases["testing"]
            assert skills_list == sorted(skills_list)

    def test_custom_min_frequency(self) -> None:
        """Should respect custom min_frequency setting."""
        extractor = KeywordExtractor(min_frequency=1)
        skills = [
            {
                "name": "unique-skill",
                "source_path": "/x.md",
                "description": "unique keyword foobar",
            }
        ]
        extracted = extractor.extract_from_skills(skills)
        alias_map = extractor.build_alias_map(extracted)

        # With min_frequency=1, even single occurrence should be included
        assert "foobar" in alias_map.aliases or "unique" in alias_map.aliases

    def test_custom_max_skills_per_alias(self) -> None:
        """Should respect custom max_skills_per_alias setting."""
        extractor = KeywordExtractor(max_skills_per_alias=3)
        skills = [
            {
                "name": f"common-skill-{i}",
                "source_path": f"/{i}.md",
                "description": "common keyword",
            }
            for i in range(10)
        ]
        extracted = extractor.extract_from_skills(skills)
        alias_map = extractor.build_alias_map(extracted)

        if "common" in alias_map.aliases:
            assert len(alias_map.aliases["common"]) <= 3

    def test_skill_without_description(self, extractor: KeywordExtractor) -> None:
        """Should handle skills without description."""
        skill = {
            "name": "minimal-skill",
            "source_path": "/path.md",
            "description": "",
        }
        result = extractor.extract_from_skill(skill)
        assert result is not None
        assert result.skill_name == "minimal-skill"
        # Should at least have tokens from name
        assert "minimal" in result.keywords or "skill" in result.keywords


class TestConstants:
    """Tests for module constants."""

    def test_stopwords_en_contains_expected(self) -> None:
        """English stopwords should contain expected words."""
        assert "use" in STOPWORDS_EN
        assert "using" in STOPWORDS_EN
        assert "used" in STOPWORDS_EN
        assert "when" in STOPWORDS_EN
        assert "with" in STOPWORDS_EN
        assert "before" in STOPWORDS_EN
        assert "after" in STOPWORDS_EN
        assert "help" in STOPWORDS_EN
        assert "task" in STOPWORDS_EN
        assert "asks" in STOPWORDS_EN
        assert "user" in STOPWORDS_EN
        assert "apply" in STOPWORDS_EN
        assert "general" in STOPWORDS_EN
        assert "specific" in STOPWORDS_EN

    def test_stopwords_es_contains_expected(self) -> None:
        """Spanish stopwords should contain expected words."""
        assert "usar" in STOPWORDS_ES
        assert "cuando" in STOPWORDS_ES
        assert "antes" in STOPWORDS_ES
        assert "después" in STOPWORDS_ES
        assert "para" in STOPWORDS_ES
        assert "sobre" in STOPWORDS_ES
        assert "tarea" in STOPWORDS_ES
        assert "usuario" in STOPWORDS_ES

    def test_short_token_whitelist(self) -> None:
        """Whitelist should contain expected short tokens."""
        assert "tdd" in SHORT_TOKEN_WHITELIST
        assert "sql" in SHORT_TOKEN_WHITELIST
        assert "api" in SHORT_TOKEN_WHITELIST
        assert "cli" in SHORT_TOKEN_WHITELIST
        assert "ui" in SHORT_TOKEN_WHITELIST
        assert "fp" in SHORT_TOKEN_WHITELIST

    def test_blacklist_contains_expected(self) -> None:
        """Blacklist should contain expected generic tokens."""
        assert "use" in BLACKLIST
        assert "using" in BLACKLIST
        assert "when" in BLACKLIST
        assert "with" in BLACKLIST
        assert "help" in BLACKLIST
        assert "task" in BLACKLIST
        assert "user" in BLACKLIST
        assert "apply" in BLACKLIST
        assert "general" in BLACKLIST
        assert "specific" in BLACKLIST
