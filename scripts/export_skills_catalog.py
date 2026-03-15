from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from src.application.keyword_extractor import KeywordExtractor
from src.infrastructure.skills_fs import discover_skills_from_paths, parse_frontmatter

ROOTS: tuple[Path, ...] = (
    Path("~/.pi/agent/skills").expanduser(),
    Path("~/.agents/skills").expanduser(),
)
OUT_DIR = Path("data/skills_catalog")
CSV_PATH = OUT_DIR / "skills_catalog.csv"


@dataclass(frozen=True)
class SkillRecord:
    skill_name: str
    skill_slug: str
    source_group: str
    path: str
    title: str
    description_raw: str
    description_brief: str
    trigger_phrases_raw: tuple[str, ...]
    trigger_terms_extracted: tuple[str, ...]


@dataclass(frozen=True)
class ExportSummary:
    exported: int
    excluded: int
    excluded_template: int
    excluded_backup: int
    excluded_other: int
    empty_description_brief: int
    empty_trigger_phrases_raw: int
    empty_trigger_terms_extracted: int
    csv_path: str


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def should_exclude(path: Path) -> str | None:
    normalized = str(path).lower()
    parts = {part.lower() for part in path.parts}
    if "template" in parts:
        return "template"
    if ".bak" in normalized or any(part.endswith(".bak") for part in parts):
        return "backup"
    return None


def detect_source_group(path: Path) -> str:
    normalized = str(path)
    if "/.pi/agent/skills/" in normalized:
        return "pi-agent"
    if "/.agents/skills/anthropic-skills/" in normalized:
        return "anthropic-skills"
    if "/.agents/skills/pi-skills/" in normalized:
        return "pi-skills"
    return "agents-other"


def extract_raw_frontmatter(content: str) -> str:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "\n".join(lines[1:index])
    return ""


def fallback_frontmatter_value(content: str, key: str) -> str:
    block = extract_raw_frontmatter(content)
    if not block:
        return ""

    lines = block.splitlines()
    prefix = f"{key}:"
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith(prefix):
            continue
        remainder = stripped[len(prefix):].strip()
        if remainder in {"|", ">", "|-", ">-"}:
            collected: list[str] = []
            for nested in lines[index + 1 :]:
                if nested.startswith((" ", "\t")):
                    collected.append(nested.strip())
                    continue
                if not nested.strip():
                    collected.append("")
                    continue
                break
            return normalize_whitespace(" ".join(collected))
        return remainder.strip('"\'')
    return ""


def extract_title(body: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return ""


def extract_first_paragraph(body: str) -> str:
    in_code = False
    parts: list[str] = []
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if not line:
            if parts:
                break
            continue
        if line.startswith("#"):
            continue
        if line.startswith(("- ", "* ", "|", ">")):
            if parts:
                break
            continue
        parts.append(line)
    return normalize_whitespace(" ".join(parts))


def first_sentence(text: str) -> str:
    cleaned = normalize_whitespace(text)
    if not cleaned:
        return ""
    return re.split(r"(?<=[.!?])\s+", cleaned)[0].strip()


def strip_trigger_lead(text: str) -> str:
    patterns = (
        r"^Use this skill whenever the user asks to\s*",
        r"^Use this skill whenever\s*",
        r"^Use this skill when\s*",
        r"^Use whenever\s*",
        r"^Use when\s*",
        r"^This skill should be used when\s*",
        r"^This skill should be used whenever\s*",
        r"^Trigger whenever\s*",
        r"^Trigger on\s*",
        r"^Helps users\s*",
    )
    cleaned = text.strip()
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip(" -:;")


def strip_boundary_clauses(text: str) -> str:
    boundary_markers = (
        "do not use",
        "don't use",
        "dont use",
        "not for",
        "not when",
        "not if",
        "prefer this over",
        "use this over",
        "use this instead",
        "instead of",
        "rather than",
        "only use",
        "only when",
        "only if",
    )
    kept: list[str] = []
    for clause in re.split(r"[.;\n]+", text):
        cleaned = normalize_whitespace(clause)
        lowered = cleaned.lower()
        if not cleaned:
            continue
        if any(marker in lowered for marker in boundary_markers):
            continue
        kept.append(cleaned)
    return normalize_whitespace(". ".join(kept))


def derive_brief_description(title: str, description_raw: str, body: str, fallback_slug: str) -> str:
    body_sentence = first_sentence(extract_first_paragraph(body))
    description_sentence = first_sentence(description_raw)
    cleaned_description = strip_trigger_lead(description_sentence)
    capability = normalize_whitespace(body_sentence or cleaned_description or description_sentence)

    if title and capability:
        if capability.lower().startswith(title.lower()):
            return capability
        return f"{title} — {capability}"
    if title:
        return title
    if capability:
        return capability
    return fallback_slug


def split_trigger_clause(clause: str) -> list[str]:
    compact = clause.replace("\n", "; ")
    compact = re.sub(r"\s+", " ", compact)
    pieces = re.split(r"\s*;\s*|\s*,\s*", compact)
    return [piece.strip(" .:-") for piece in pieces if piece.strip(" .:-")]


def dedupe_ordered(values: list[str]) -> tuple[str, ...]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = normalize_whitespace(value).strip(" .:-")
        if not normalized:
            continue
        key = normalized.casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(normalized)
    return tuple(deduped)


def extract_trigger_phrases(description_raw: str) -> tuple[str, ...]:
    phrases: list[str] = []
    text = description_raw.strip()
    if not text:
        return ()

    for quoted in re.findall(r'"([^"]+)"|`([^`]+)`', text):
        candidate = quoted[0] or quoted[1]
        if candidate:
            phrases.append(candidate)

    marker_patterns = (
        r"Triggers on:\s*(.+)",
        r"Triggers include:\s*(.+)",
        r"Triggers include\s*(.+)",
        r"Triggers when:\s*(.+)",
        r"Trigger on requests about\s*(.+?)(?:\.|$)",
        r"Trigger on\s*(.+?)(?:\.|$)",
        r"Trigger whenever\s*(.+?)(?:\.|$)",
        r"Use when\s*(.+?)(?:\.|$)",
        r"Use whenever\s*(.+?)(?:\.|$)",
        r"Use this skill when\s*(.+?)(?:\.|$)",
        r"Use this skill whenever\s*(.+?)(?:\.|$)",
        r"This skill should be used when\s*(.+?)(?:\.|$)",
        r"This skill should be used whenever\s*(.+?)(?:\.|$)",
    )
    for pattern in marker_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match is not None:
            phrases.extend(split_trigger_clause(match.group(1)))

    if "Triggers when:" in text:
        trigger_section = text.split("Triggers when:", maxsplit=1)[1]
        for line in trigger_section.splitlines():
            stripped = line.strip()
            if stripped.startswith("-"):
                phrases.append(stripped.lstrip("- "))

    return dedupe_ordered(phrases)


def build_records() -> tuple[list[SkillRecord], ExportSummary]:
    discovered = discover_skills_from_paths(list(ROOTS))
    extractor = KeywordExtractor(min_frequency=1, max_skills_per_alias=9999)

    records: list[SkillRecord] = []
    excluded_template = 0
    excluded_backup = 0
    excluded_other = 0

    for skill in discovered:
        exclusion_reason = should_exclude(skill.path)
        if exclusion_reason == "template":
            excluded_template += 1
            continue
        if exclusion_reason == "backup":
            excluded_backup += 1
            continue
        if exclusion_reason is not None:
            excluded_other += 1
            continue

        _, body = parse_frontmatter(skill.content)
        title = extract_title(body)
        skill_name = skill.meta.name or fallback_frontmatter_value(skill.content, "name") or skill.path.parent.name
        description_raw = normalize_whitespace(
            skill.meta.description or fallback_frontmatter_value(skill.content, "description")
        )
        if not description_raw:
            description_raw = normalize_whitespace(extract_first_paragraph(body))

        extracted = extractor.extract_from_skill(
            {
                "name": skill_name,
                "source_path": str(skill.path),
                "description": strip_boundary_clauses(description_raw) or description_raw,
            }
        )
        trigger_terms_extracted = tuple(sorted(extracted.keywords)) if extracted else ()
        trigger_phrases_raw = extract_trigger_phrases(description_raw)
        record = SkillRecord(
            skill_name=skill_name,
            skill_slug=skill.path.parent.name,
            source_group=detect_source_group(skill.path),
            path=str(skill.path),
            title=title,
            description_raw=description_raw,
            description_brief=derive_brief_description(
                title=title,
                description_raw=description_raw,
                body=body,
                fallback_slug=skill.path.parent.name,
            ),
            trigger_phrases_raw=trigger_phrases_raw,
            trigger_terms_extracted=trigger_terms_extracted,
        )
        records.append(record)

    records.sort(key=lambda item: (item.source_group, item.skill_name.casefold(), item.path.casefold()))

    summary = ExportSummary(
        exported=len(records),
        excluded=excluded_template + excluded_backup + excluded_other,
        excluded_template=excluded_template,
        excluded_backup=excluded_backup,
        excluded_other=excluded_other,
        empty_description_brief=sum(1 for item in records if not item.description_brief),
        empty_trigger_phrases_raw=sum(1 for item in records if not item.trigger_phrases_raw),
        empty_trigger_terms_extracted=sum(1 for item in records if not item.trigger_terms_extracted),
        csv_path=str(CSV_PATH),
    )
    return records, summary


def write_csv(records: list[SkillRecord]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "skill_name",
                "skill_slug",
                "source_group",
                "path",
                "title",
                "description_raw",
                "description_brief",
                "trigger_phrases_raw",
                "trigger_terms_extracted",
                "trigger_count",
            ]
        )
        for record in records:
            trigger_count = len(set(record.trigger_phrases_raw) | set(record.trigger_terms_extracted))
            writer.writerow(
                [
                    record.skill_name,
                    record.skill_slug,
                    record.source_group,
                    record.path,
                    record.title,
                    record.description_raw,
                    record.description_brief,
                    " | ".join(record.trigger_phrases_raw),
                    " | ".join(record.trigger_terms_extracted),
                    trigger_count,
                ]
            )


def print_summary(summary: ExportSummary) -> None:
    print(f"exported={summary.exported}")
    print(f"excluded={summary.excluded}")
    print(f"excluded_template={summary.excluded_template}")
    print(f"excluded_backup={summary.excluded_backup}")
    print(f"excluded_other={summary.excluded_other}")
    print(f"empty_description_brief={summary.empty_description_brief}")
    print(f"empty_trigger_phrases_raw={summary.empty_trigger_phrases_raw}")
    print(f"empty_trigger_terms_extracted={summary.empty_trigger_terms_extracted}")
    print(f"csv={summary.csv_path}")


def main() -> None:
    records, summary = build_records()
    write_csv(records)
    print_summary(summary)


if __name__ == "__main__":
    main()
