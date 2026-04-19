# 03-trifecta-infra.md

Documentation of the `trifecta_dope` infrastructure powering `skill-hub`.

### 1. skill_hub_indexing_strategy.py
- **Path:** `~/Developer/agent_h/trifecta_dope/src/application/skill_hub_indexing_strategy.py`
- **Purpose:** Manifest-driven indexing strategy for `skill_hub` segments, ensuring only canonical skills from `skills_manifest.json` are indexed.
- **Key classes/functions:**
    - `SkillHubIndexingStrategy`: Main class for building context packs.
    - `build()`: High-level entry point that detects policy and loads manifest.
    - `build_from_manifest(manifest)`: Core logic to convert manifest entries into `ContextChunk` and `ContextPack`.

```python
class SkillHubIndexingStrategy:
    def build_from_manifest(self, manifest: SkillManifest) -> Result[ContextPack, list[str]]:
        """Build context pack from an already-admitted manifest."""
        # ... validation ...
        for skill_entry in manifest.skills:
            if not skill_entry.canonical:
                continue

            skill_file_path = self.segment_path / skill_entry.relative_path
            content = skill_file_path.read_text(encoding="utf-8")
            
            # Build chunk
            chunk = ContextChunk(
                id=skill_entry.chunk_id,
                doc="skill",
                title_path=[skill_file_path.name],
                text=content,
                source_path=skill_entry.relative_path,
                chunking_method="whole_file",
            )
            chunks.append(chunk)
        # ...
        return Ok(ContextPack(..., chunks=chunks, ...))
```
- **Data Flow:** Receives a segment path -> Loads `skills_manifest.json` -> Reads SKILL.md files -> Generates `ContextChunk` and `ContextPack` for indexing.

---

### 2. skill_lint_use_case.py
- **Path:** `~/Developer/agent_h/trifecta_dope/src/application/skill_lint_use_case.py`
- **Purpose:** Orchestrates the skill validation/linting pipeline by combining discovery and domain validation.
- **Key classes/functions:**
    - `lint_skills(paths)`: Main function to lint all skills in provided paths.
    - `SkillLintResult`: Dataclass containing per-skill validation state.
    - `SkillLintReport`: Aggregated report for multiple skills.

```python
def lint_skills(paths: list[Path]) -> SkillLintReport:
    """Lint all skills in the given paths."""
    discovered = discover_skills_from_paths(paths)
    results: list[SkillLintResult] = []

    for skill in discovered:
        validation = validate_skill_meta(skill.meta)
        if validation.is_ok():
            results.append(SkillLintResult(path=str(skill.path), name=skill.meta.name, valid=True, errors=[]))
        else:
            match validation:
                case Err(errs):
                    results.append(SkillLintResult(path=str(skill.path), name=skill.meta.name, valid=False, errors=errs))
    
    return SkillLintReport(skills=results, total=len(results), ...)
```
- **Data Flow:** CLI calls `lint_skills` -> Uses `skills_fs` to find files -> Uses `skill_contracts` to validate -> Returns structured report for CLI rendering.

---

### 3. skills_fs.py
- **Path:** `~/Developer/agent_h/trifecta_dope/src/infrastructure/skills_fs.py`
- **Purpose:** Infrastructure layer for file system operations, specialized in discovering `SKILL.md` files and extracting their YAML frontmatter.
- **Key classes/functions:**
    - `discover_skills_from_paths(paths)`: Recursive discovery of `SKILL.md` files.
    - `parse_frontmatter(content)`: Extracts YAML block from markdown.
    - `dict_to_skill_meta(data)`: Bridges YAML data to the `SkillMeta` domain model.

```python
def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from markdown content."""
    lines = content.strip().split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, content

    end_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    frontmatter_text = "\n".join(lines[1:end_idx])
    body = "\n".join(lines[end_idx + 1 :])
    frontmatter = yaml.safe_load(frontmatter_text) or {}
    return frontmatter, body
```
- **Data Flow:** Scans disk for `SKILL.md` -> Reads content -> Parses YAML -> Hydrates `SkillMeta` domain entities.

---

### 4. skill_cards.py
- **Path:** `~/Developer/agent_h/trifecta_dope/src/cli/skill_cards.py`
- **Purpose:** Rendering engine for skill cards using the Rich library, strictly adhering to a 4px grid design system.
- **Key classes/functions:**
    - `SkillCard`: Immutable data model for card rendering.
    - `render_card(card, style)`: Renders a single card (rich, compact, or plain).
    - `parse_skill_from_chunk(chunk_text, chunk_id)`: Extracts `SkillCard` data from indexed context chunks.

```python
def _render_rich(card: SkillCard, file: IO[str] | None = None) -> None:
    """Rich Panel card with full visual hierarchy."""
    # ... header assembly with relevance bar ...
    # ... body assembly with triggers and command ...
    panel = Panel(
        body,
        title=header,
        border_style=BORDER_SUBTLE,
        box=box.ROUNDED,
        padding=(SPACE_1, SPACE_2),
        expand=False,
    )
    console.print(panel)
```
- **Data Flow:** Receives `SkillCard` (or raw chunk text) -> Applies design tokens (colors, spacing) -> Outputs formatted panel to TTY or plain text to agents.

---

### 5. cli_skills.py
- **Path:** `~/Developer/agent_h/trifecta_dope/src/infrastructure/cli_skills.py`
- **Purpose:** CLI implementation for skill-related tasks, specifically automated keyword/alias extraction for the `skill-hub`.
- **Key classes/functions:**
    - `run_extract_keywords(...)`: Core logic for generating `aliases.generated.yaml`.
    - `skills_app`: Typer application for skill commands (standalone/testing).

```python
def run_extract_keywords(segment, output, min_frequency, max_skills_per_alias, stdout, dry_run, check):
    """Run the extract-keywords command."""
    skills = load_skills_manifest(segment_path)
    extractor = KeywordExtractor(min_frequency=min_frequency, max_skills_per_alias=max_skills_per_alias)
    
    extracted = extractor.extract_from_skills(skills)
    alias_map = extractor.build_alias_map(extracted)
    
    if not dry_run and not stdout:
        writer = GeneratedAliasWriter(segment_path=segment_path, output_path=output_path)
        writer.write(alias_map.aliases)
```
- **Data Flow:** Manifest-loaded skills -> NLP-based keyword extraction -> Frequency analysis -> YAML persistence in `_ctx/aliases.generated.yaml`.

---

### 6. skill_contracts.py
- **Path:** `~/Developer/agent_h/trifecta_dope/src/domain/skill_contracts.py`
- **Purpose:** Domain layer defining the structure and validation rules for skills and their parameters.
- **Key classes/functions:**
    - `SkillMeta`: The core entity for skill metadata.
    - `SkillInput`: Specification for skill parameters.
    - `validate_skill_meta(meta)`: Validates names, descriptions, and structural integrity.

```python
def validate_skill_meta(meta: SkillMeta) -> Result[SkillMeta, list[SkillValidationError]]:
    """Validate skill metadata."""
    errors: list[SkillValidationError] = []
    if not meta.name or not meta.name.strip():
        errors.append(SkillValidationError("name", "name cannot be empty"))
    if not meta.description or not meta.description.strip():
        errors.append(SkillValidationError("description", "description cannot be empty"))
    
    for i, inp in enumerate(meta.inputs):
        inp_result = validate_skill_input(inp)
        # ... error aggregation ...
    return Err(errors) if errors else Ok(meta)
```
- **Data Flow:** Acts as the Single Source of Truth for "what a skill is" across all layers; used by `skills_fs` for hydration and `skill_lint_use_case` for validation.
