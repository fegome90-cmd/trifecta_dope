"""Keyword extraction from skill metadata for alias generation.

This module provides deterministic, testable extraction of keywords from
skill names and descriptions to generate alias mappings for query expansion.

Design principles (v1):
- NO NLP advanced (no POS tagging, no lemmatization, no embeddings)
- Deterministic output (same input -> same output)
- Simple tokenization from kebab/snake/camel case
- Stopword filtering (English + Spanish)
- Blacklist for generic terms
- Whitelist for short technical tokens
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

# Minimum token length (unless whitelisted)
MIN_TOKEN_LENGTH = 3

# Default frequency threshold
DEFAULT_MIN_FREQUENCY = 2

# Default cap per alias
DEFAULT_MAX_SKILLS_PER_ALIAS = 8

# English stopwords (plan-specified)
STOPWORDS_EN: frozenset[str] = frozenset({
    "use", "using", "used", "when", "with", "before", "after",
    "help", "task", "asks", "user", "apply", "general", "specific",
    "the", "and", "for", "to", "of", "a", "an", "is", "are", "was",
    "were", "be", "been", "being", "have", "has", "had", "do", "does",
    "did", "will", "would", "could", "should", "may", "might", "must",
    "shall", "can", "need", "dare", "ought", "used", "this", "that",
    "these", "those", "am", "i", "you", "he", "she", "it", "we", "they",
    "what", "which", "who", "whom", "whose", "where", "why", "how",
    "all", "each", "every", "both", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "just", "also", "now", "here", "there",
    "then", "once", "from", "into", "during", "including", "until",
    "against", "among", "throughout", "despite", "towards", "upon",
    "per", "via", "etc", "like",
})

# Spanish stopwords (plan-specified)
STOPWORDS_ES: frozenset[str] = frozenset({
    "usar", "cuando", "antes", "después", "para", "sobre", "tarea",
    "usuario", "el", "la", "los", "las", "un", "una", "unos", "unas",
    "de", "del", "al", "a", "en", "con", "por", "es", "son", "fue",
    "ser", "tiene", "han", "hay", "esto", "eso", "aquello", "este",
    "ese", "aquel", "como", "más", "muy", "sin", "sobre", "también",
    "ya", "desde", "todo", "pero", "mismo", "si", "porque", "hasta",
    "yo", "tú", "él", "ella", "nosotros", "ellos", "ellas", "qué",
    "quién", "dónde", "cuándo", "cómo", "cuál", "cuales", "cuánto",
    "entre", "durante", "mediante", "según", "contra", "hacia",
})

# Combined stopwords
STOPWORDS_ALL: frozenset[str] = STOPWORDS_EN | STOPWORDS_ES

# Whitelist for short tokens (plan-specified)
SHORT_TOKEN_WHITELIST: frozenset[str] = frozenset({
    "tdd", "sql", "api", "cli", "ui", "fp", "go", "rs", "js", "ts",
    "db", "id", "io", "os", "ai", "ml", "dl", "nn", "nlp", "cv",
    "ci", "cd", "pr", "mr", "cr", "ux", "qa", "sl", "rl", "hr",
})

# Blacklist for generic terms (plan-specified)
BLACKLIST: frozenset[str] = frozenset({
    "use", "using", "used", "when", "with", "before", "after",
    "help", "task", "asks", "user", "apply", "general", "specific",
    "provide", "provides", "provided", "following", "follows", "follow",
    "create", "creates", "created", "creating", "make", "makes", "made",
    "get", "gets", "getting", "set", "sets", "setting", "put", "puts",
    "take", "takes", "taking", "give", "gives", "giving", "given",
    "want", "wants", "wanted", "needing", "need", "needs", "needed",
    "ensure", "ensures", "ensured", "ensuring", "check", "checks",
    "checked", "checking", "verify", "verifies", "verified", "verifying",
    "based", "support", "supports", "supported", "supporting",
    "include", "includes", "included", "including", "contain", "contains",
    "contained", "containing", "handle", "handles", "handled", "handling",
    "manage", "manages", "managed", "managing", "implement", "implements",
    "implemented", "implementing", "implementation", "implementations",
})


def extract_name_tokens(name: str) -> frozenset[str]:
    """Extract tokens from a skill name.

    Handles kebab-case, snake_case, camelCase, and PascalCase.

    Args:
        name: The skill name to tokenize.

    Returns:
        Frozenset of lowercase tokens.
    """
    if not name:
        return frozenset()

    # Replace separators with spaces
    normalized = name.replace("-", " ").replace("_", " ")

    # Split camelCase and PascalCase
    # Insert space before uppercase letters that follow lowercase
    normalized = re.sub(r"([a-z])([A-Z])", r"\1 \2", normalized)

    # Split consecutive capitals followed by lowercase (e.g., "XMLParser" -> "XML Parser")
    normalized = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", normalized)

    # Tokenize and normalize
    tokens: set[str] = set()
    for token in normalized.split():
        token_lower = token.lower().strip()
        if token_lower:
            tokens.add(token_lower)

    return frozenset(tokens)


def normalize_token(token: str) -> str | None:
    """Normalize and filter a single token.

    Args:
        token: The token to normalize.

    Returns:
        Normalized token, or None if filtered out.
    """
    # Lowercase and trim
    normalized = token.lower().strip()

    # Remove peripheral punctuation
    normalized = normalized.strip('.,!?;:"\'()[]{}<>`~@#$%^&*-+=|\\/')

    if not normalized:
        return None

    # Check stopwords
    if normalized in STOPWORDS_ALL:
        return None

    # Check blacklist
    if normalized in BLACKLIST:
        return None

    # Check minimum length
    if len(normalized) < MIN_TOKEN_LENGTH:
        # Allow if in whitelist
        if normalized not in SHORT_TOKEN_WHITELIST:
            return None

    return normalized


def tokenize_description(description: str) -> list[str]:
    """Tokenize and filter a skill description.

    Args:
        description: The description text to tokenize.

    Returns:
        List of normalized, filtered tokens (deduplicated, order preserved).
    """
    if not description:
        return []

    # Split on whitespace and punctuation
    raw_tokens = re.split(r"[\s,.;:!?\-–—]+", description)

    seen: set[str] = set()
    result: list[str] = []

    for raw_token in raw_tokens:
        normalized = normalize_token(raw_token)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)

    return result


@dataclass(frozen=True)
class ExtractedSkillKeywords:
    """Keywords extracted from a single skill.

    Attributes:
        skill_name: The skill's name (used as skill_id).
        source_path: Path to the skill file.
        keywords: Frozenset of extracted keywords.
    """

    skill_name: str
    source_path: str
    keywords: frozenset[str]


@dataclass(frozen=True)
class GeneratedAliasMap:
    """Generated alias mapping.

    Attributes:
        schema_version: Schema version (always 1 for AliasLoader compatibility).
        aliases: Dict mapping keywords to lists of skill names.
    """

    schema_version: int = 1
    aliases: dict[str, list[str]] = field(default_factory=dict)


class KeywordExtractor:
    """Extract keywords from skill metadata and build alias maps.

    This class orchestrates the extraction pipeline:
    1. Extract tokens from skill names
    2. Extract tokens from descriptions
    3. Apply frequency filtering
    4. Build alias map with caps

    Attributes:
        min_frequency: Minimum frequency for a keyword to be included.
        max_skills_per_alias: Maximum skills per alias (cap).
    """

    def __init__(
        self,
        min_frequency: int = DEFAULT_MIN_FREQUENCY,
        max_skills_per_alias: int = DEFAULT_MAX_SKILLS_PER_ALIAS,
    ) -> None:
        """Initialize the extractor.

        Args:
            min_frequency: Minimum frequency threshold.
            max_skills_per_alias: Cap for skills per alias.
        """
        self.min_frequency = min_frequency
        self.max_skills_per_alias = max_skills_per_alias

    def extract_from_skill(self, skill: dict[str, str]) -> ExtractedSkillKeywords | None:
        """Extract keywords from a single skill.

        Args:
            skill: Dict with 'name', 'source_path', and 'description' keys.

        Returns:
            ExtractedSkillKeywords or None if skill has no extractable content.
        """
        name = skill.get("name", "")
        source_path = skill.get("source_path", "")
        description = skill.get("description", "")

        if not name:
            return None

        # Extract tokens from name
        name_tokens = extract_name_tokens(name)

        # Extract tokens from description
        desc_tokens = tokenize_description(description)

        # Combine all tokens
        all_keywords = name_tokens | frozenset(desc_tokens)

        # Filter through normalize_token to apply all rules
        filtered_keywords: set[str] = set()
        for kw in all_keywords:
            normalized = normalize_token(kw)
            if normalized:
                filtered_keywords.add(normalized)

        return ExtractedSkillKeywords(
            skill_name=name,
            source_path=source_path,
            keywords=frozenset(filtered_keywords),
        )

    def extract_from_skills(
        self, skills: Sequence[dict[str, str]]
    ) -> list[ExtractedSkillKeywords]:
        """Extract keywords from multiple skills.

        Args:
            skills: Sequence of skill dicts.

        Returns:
            List of ExtractedSkillKeywords (excludes None results).
        """
        results: list[ExtractedSkillKeywords] = []
        for skill in skills:
            result = self.extract_from_skill(skill)
            if result:
                results.append(result)
        return results

    def build_alias_map(
        self, extracted: Sequence[ExtractedSkillKeywords]
    ) -> GeneratedAliasMap:
        """Build alias map from extracted keywords.

        Applies:
        - Frequency filtering (min_frequency)
        - Cap per alias (max_skills_per_alias)
        - Deterministic ordering (alphabetical)

        Args:
            extracted: Sequence of ExtractedSkillKeywords.

        Returns:
            GeneratedAliasMap with filtered aliases.
        """
        # Build keyword -> skills mapping
        keyword_to_skills: dict[str, set[str]] = {}

        for skill_kw in extracted:
            for keyword in skill_kw.keywords:
                if keyword not in keyword_to_skills:
                    keyword_to_skills[keyword] = set()
                keyword_to_skills[keyword].add(skill_kw.skill_name)

        # Apply frequency filter and cap
        aliases: dict[str, list[str]] = {}

        for keyword, skills in keyword_to_skills.items():
            # Frequency filter
            if len(skills) < self.min_frequency:
                continue

            # Sort for determinism
            sorted_skills = sorted(skills)

            # Apply cap
            capped_skills = sorted_skills[: self.max_skills_per_alias]

            aliases[keyword] = capped_skills

        return GeneratedAliasMap(schema_version=1, aliases=aliases)
