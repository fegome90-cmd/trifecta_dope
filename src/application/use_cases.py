import json
import subprocess
import yaml  # type: ignore[import-untyped]
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from src.domain.models import TrifectaConfig, TrifectaPack, ValidationResult
from src.domain.context_models import (
    ContextPack,
    ContextChunk,
    ContextIndexEntry,
    SourceFile,
    SearchResult,
    GetResult,
)
from src.domain.constants import MAX_SKILL_LINES
from src.infrastructure.templates import TemplateRenderer
from src.infrastructure.file_system import FileSystemAdapter
from src.infrastructure.file_system_utils import AtomicWriter, file_lock
from src.application.context_service import ContextService


class CreateTrifectaUseCase:
    """Create a new Trifecta pack."""

    def __init__(
        self,
        template_renderer: TemplateRenderer,
        file_system: FileSystemAdapter,
    ):
        self.template_renderer = template_renderer
        self.file_system = file_system

    def execute(
        self,
        config: TrifectaConfig,
        target_path: Path,
        docs: list[str],
        dry_run: bool = False,
    ) -> TrifectaPack:
        """Generate and save a Trifecta pack.

        Args:
            config: Trifecta configuration
            target_path: Target directory path
            docs: List of documentation files
            dry_run: If True, generate but don't save files

        Returns:
            TrifectaPack with generated content
        """
        pack = TrifectaPack(
            config=config,
            skill_content=self.template_renderer.render_skill(config),
            prime_content=self.template_renderer.render_prime(config, docs),
            agent_content=self.template_renderer.render_agent(config),
            session_content=self.template_renderer.render_session(config),
            readme_content=self.template_renderer.render_readme(config),
        )

        # Validate before saving
        if pack.skill_line_count > MAX_SKILL_LINES:
            raise ValueError(f"skill.md exceeds {MAX_SKILL_LINES} lines ({pack.skill_line_count})")

        # Save files (skip if dry_run)
        if not dry_run:
            self.file_system.save_trifecta(target_path, pack)

        return pack


class ValidateTrifectaUseCase:
    """Validate an existing Trifecta pack."""

    def __init__(self, file_system: FileSystemAdapter):
        self.file_system = file_system

    def execute(self, target_path: Path) -> ValidationResult:
        """Validate a Trifecta pack structure and content."""
        errors: list[str] = []
        warnings: list[str] = []

        # Check skill.md
        skill_path = target_path / "skill.md"
        if not skill_path.exists():
            errors.append("Missing: skill.md")
        else:
            content = skill_path.read_text()
            line_count = len(content.strip().split("\n"))
            if line_count > MAX_SKILL_LINES:
                errors.append(f"skill.md exceeds {MAX_SKILL_LINES} lines ({line_count})")

        # Check _ctx directory
        ctx_dir = target_path / "_ctx"
        if not ctx_dir.exists():
            errors.append("Missing: _ctx/ directory")
        else:
            prime_files = list(ctx_dir.glob("prime_*.md"))
            if not prime_files:
                errors.append("Missing: _ctx/prime_*.md")

            agent_path = ctx_dir / "agent.md"
            if not agent_path.exists():
                errors.append("Missing: _ctx/agent.md")

            session_files = list(ctx_dir.glob("session_*.md"))
            if not session_files:
                warnings.append("Missing: _ctx/session_*.md (optional but recommended)")

        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )


class RefreshPrimeUseCase:
    """Refresh prime_*.md by re-scanning docs."""

    def __init__(
        self,
        template_renderer: TemplateRenderer,
        file_system: FileSystemAdapter,
    ):
        self.template_renderer = template_renderer
        self.file_system = file_system

    def execute(
        self,
        target_path: Path,
        scan_path: Path,
        repo_root: Path,
    ) -> str:
        """Re-scan docs and update prime file."""
        ctx_dir = target_path / "_ctx"
        prime_files = list(ctx_dir.glob("prime_*.md"))

        if not prime_files:
            raise FileNotFoundError("No prime_*.md found. Run 'create' first.")

        prime_path = prime_files[0]
        segment = prime_path.stem.replace("prime_", "")

        # Scan docs
        docs = self.file_system.scan_docs(scan_path, repo_root)

        # Build minimal config
        config = TrifectaConfig(
            segment=segment,
            scope=f"Segment {segment}",
            repo_root=str(repo_root),
        )

        # Regenerate prime
        prime_content = self.template_renderer.render_prime(config, docs)
        prime_path.write_text(prime_content)

        return prime_path.name
class BuildContextPackUseCase:
    """Build a Context Pack for a segment."""

    def __init__(self, file_system: FileSystemAdapter, telemetry: Any = None) -> None:
        self.file_system = file_system
        self.telemetry = telemetry

    def _extract_references(
        self, content: str, root: Path, repo_root: Path | None = None
    ) -> dict[str, Path]:
        """Extract referenced files from Prime content with STRICT SECURITY."""
        import re

        refs: dict[str, Path] = {}
        visited_paths = set()
        MAX_LINKS = 25

        # Regex for [link](path) and `path`
        lines = content.splitlines()
        for line in lines:
            line = line.strip()
            if not (line.startswith("-") or line.startswith("*") or line[0:1].isdigit()):
                continue

            path_str = None
            # Try `code` block
            code_match = re.search(r"`([^`]+)`", line)
            if code_match:
                path_str = code_match.group(1).strip()

            # Try [link](path)
            link_match = re.search(r"\[.*?\]\((.*?)\)", line)
            if link_match:
                path_str = link_match.group(1).strip()

            if path_str:
                if len(refs) >= MAX_LINKS:
                    warning_msg = f"prime_links_truncated_total"
                    if self.telemetry:
                        self.telemetry.incr(warning_msg)
                    print(
                        f"⚠️ Warning: Max links ({MAX_LINKS}) reached in Prime. Skipping remainder."
                    )
                    break

                if self._is_valid_ref(path_str):
                    resolved = self._resolve_path(path_str, root, repo_root)

                    if resolved:
                        # Cycle/Duplicate Check
                        abs_path = str(resolved.resolve())
                        if abs_path in visited_paths:
                            if self.telemetry:
                                self.telemetry.incr("prime_links_cycle_total")
                            print(
                                f"⚠️ Warning: Cycle/Duplicate detected for '{path_str}'. Skipping."
                            )
                            continue

                        # Security Scope Check
                        if self._is_safe_path(resolved, root):
                            refs[path_str] = resolved
                            visited_paths.add(abs_path)
                            if self.telemetry:
                                self.telemetry.incr("prime_links_included_total")
                        else:
                            # Policy: FAIL-CLOSED (PCC enforcement)
                            if self.telemetry:
                                self.telemetry.incr("prime_links_skipped_security_total")
                            error_msg = f"PROHIBITED: Reference '{path_str}' resolves outside segment or in forbidden path."
                            print(f"❌ {error_msg}")
                            raise ValueError(error_msg)

        return refs

    def _validate_prohibited_paths(self, files: list[Path]) -> None:
        """Fail-closed: Reject any file that looks like code or is in prohibited dirs."""
        import sys

        for f in files:
            path_str = str(f).lower()
            if (
                "/src/" in path_str
                or "src/" in path_str
                or f.suffix in [".py", ".ts", ".js", ".go", ".rs"]
            ):
                print(f"❌ PROHIBITED: Cannot index code files in pack: {f}", file=sys.stderr)
                print(
                    "Trifecta is Programming Context Calling (meta-first), not RAG.",
                    file=sys.stderr,
                )
                print("Code access MUST be via curated prime links in meta-docs.", file=sys.stderr)
                # In UseCase, we raise ValueError instead of sys.exit
                raise ValueError(f"Prohibited file in context pack: {f}")

    def _is_valid_ref(self, path_str: str) -> bool:
        if "://" in path_str or not path_str or path_str.startswith("#"):
            return False
        # Allowlist: MD only for now
        return path_str.endswith(".md")

    def _is_safe_path(self, path: Path, root: Path) -> bool:
        """Prevent path traversal. Must be within segment."""
        # Resolves symlinks to ensure we don't escape
        try:
            resolved_path = path.resolve()
            resolved_root = root.resolve()
            return resolved_path.is_relative_to(resolved_root)
        except ValueError:
            return False

    def _resolve_path(self, path_str: str, root: Path, repo_root: Path | None) -> Path | None:
        # 1. Try relative to component root
        p = root / path_str
        if p.exists() and p.is_file():
            return p

        # 2. Try relative to REPO_ROOT (if known) -- BUT ONLY if it resolves inside segment
        # (This effectively disables repo-root links unless they point back into segment,
        # complying with "Scope limited to segment")
        if repo_root:
            p = repo_root / path_str
            if p.exists() and p.is_file():
                return p

        return None

    def execute(self, target_path: Path) -> ContextPack:
        if self.telemetry:
            self.telemetry.incr("ctx_build_count")
        """Scan a Trifecta segment and build a context_pack.json."""
        # 1. Detect segment name from path or prime file
        ctx_dir = target_path / "_ctx"
        prime_files = list(ctx_dir.glob("prime_*.md"))
        if not prime_files:
            raise FileNotFoundError("No prime_*.md found. Run 'create' first.")

        prime_path = prime_files[0]
        segment = prime_path.stem.replace("prime_", "")

        # Try to parse REPO_ROOT from prime header
        repo_root = None
        prime_content = prime_path.read_text()
        import re

        rr_match = re.search(r">\s*\*\*REPO_ROOT\*\*:\s*`?([^`\n]+)`?", prime_content)
        if rr_match:
            try:
                repo_root = Path(rr_match.group(1).strip())
            except:
                pass

        # 2. Identify source files
        sources = {
            "skill": target_path / "skill.md",
            "agent": ctx_dir / "agent.md",
            "prime": prime_path,
        }

        # Add session file if it exists
        session_files = list(ctx_dir.glob("session_*.md"))
        if session_files:
            sources["session"] = session_files[0]

        # 2.5 Extract references from Prime
        refs = self._extract_references(prime_content, target_path, repo_root)
        
        # Compute primary source paths for exclusion (path-aware deduplication)
        primary_skill_path = target_path / "skill.md"
        excluded_paths = {primary_skill_path.resolve()}
        
        for name, path in refs.items():
            # Skip if this exact path is already indexed as a primary source
            if path.resolve() in excluded_paths:
                continue
            sources[f"ref:{name}"] = path

        # 2.6 FAIL-CLOSED VALIDATION
        self._validate_prohibited_paths(list(sources.values()))

        chunks: list[ContextChunk] = []
        index: list[ContextIndexEntry] = []
        source_files: list[SourceFile] = []

        # 3. Process each file as a whole_file chunk (MVP)
        for doc_type, file_path in sources.items():
            if not file_path.exists():
                continue

            content = file_path.read_text()
            # Simple token estimation: 4 chars per token
            token_est = len(content) // 4

            # Source metadata
            import hashlib

            sha256 = hashlib.sha256(content.encode()).hexdigest()
            mtime = file_path.stat().st_mtime
            source_files.append(
                SourceFile(
                    path=str(file_path.relative_to(target_path.parent)),
                    sha256=sha256,
                    mtime=mtime,
                    chars=len(content),
                )
                if target_path.parent in file_path.parents
                else SourceFile(path=file_path.name, sha256=sha256, mtime=mtime, chars=len(content))
            )

            # Stable ID: doc:sha1(doc + "\n" + title_path_norm + "\n" + text_sha256)[:10]
            title_path_norm = file_path.name
            id_input = f"{doc_type}\n{title_path_norm}\n{sha256}"
            content_hash = hashlib.sha1(id_input.encode()).hexdigest()[:10]
            chunk_id = f"{doc_type}:{content_hash}"

            chunk = ContextChunk(
                id=chunk_id,
                doc=doc_type,
                title_path=[file_path.name],
                text=content,
                char_count=len(content),
                token_est=token_est,
                source_path=str(file_path.name),  # Minimal for MVP
                chunking_method="whole_file",
            )
            chunks.append(chunk)

            # Index entry (L0)
            preview = content[:200].strip() + "..." if len(content) > 200 else content
            index.append(
                ContextIndexEntry(
                    id=chunk_id,
                    title_path_norm=title_path_norm,
                    preview=preview,
                    token_est=token_est,
                )
            )

        pack = ContextPack(segment=segment, source_files=source_files, chunks=chunks, index=index)

        # 4. Save to disk atomically with lock
        pack_path = ctx_dir / "context_pack.json"
        lock_path = ctx_dir / ".autopilot.lock"

        with file_lock(lock_path):
            AtomicWriter.write(pack_path, pack.model_dump_json(indent=2))

        return pack


class MacroLoadUseCase:
    """Macro command 'trifecta load' implementation."""

    def __init__(self, file_system: FileSystemAdapter, telemetry: Any = None) -> None:
        self.file_system = file_system
        self.telemetry = telemetry

    def execute(self, target_path: Path, task: str, mode: str = "pcc") -> str:
        """Execute the macro load logic using Plan A (API) or Plan B (Fallback)."""
        ctx_dir = target_path / "_ctx"
        pack_path = ctx_dir / "context_pack.json"

        # Force Fallback if mode is fullfiles or pack missing
        if mode == "fullfiles" or not pack_path.exists():
            # FALLBACK (Plan B): Traditional file selection
            return self._fallback_load(target_path, task)

        # 1. Expand task with aliases for discovery
        from src.infrastructure.alias_loader import AliasLoader
        from src.application.query_normalizer import QueryNormalizer
        from src.application.query_expander import QueryExpander

        alias_loader = AliasLoader(target_path)
        aliases = alias_loader.load()

        norm_task = QueryNormalizer.normalize(task)
        tokens = QueryNormalizer.tokenize(norm_task)
        expander = QueryExpander(aliases)
        expanded_terms = expander.expand(norm_task, tokens)

        # Execute search for each expanded piece
        service = ContextService(target_path)
        combined_hits: dict[str, tuple[Any, float]] = {}  # chunk_id -> (hit, max_weighted_score)

        for term, weight in expanded_terms:
            search_res = service.search(term, k=10)
            for hit in search_res.hits:
                weighted_score = hit.score * weight
                if hit.id not in combined_hits or weighted_score > combined_hits[hit.id][1]:
                    combined_hits[hit.id] = (hit, weighted_score)

        if not combined_hits:
            # If search fails, fallback to Plan B
            return self._fallback_load(target_path, task)

        # T4: Ordena hits por "valor por token" (weighted_score/token_est)
        hits = list(combined_hits.values())
        hits.sort(key=lambda x: x[1] / max(x[0].token_est, 1), reverse=True)
        top_hits = [hit for hit, _ in hits[:5]]
        ids = [hit.id for hit in top_hits]

        # 2. Get L0 Skeletons (Initial navigation)
        l0_ids = []
        for cid in ["skill", "agent"]:
            match = [c.id for c in service._load_pack().chunks if c.id.startswith(f"{cid}:")]
            if match:
                l0_ids.append(match[0])

        l0_res = service.get(l0_ids, mode="skeleton", budget_token_est=400)

        # 3. Get Task Evidence (L1 Excerpts)
        evid_res = service.get(ids, mode="excerpt", budget_token_est=1500)

        # 4. Format output (EVIDENCE read-only style)
        output = [f"# Context Evidence for Task: {task}\n"]
        output.append("> [!NOTE]")
        output.append(
            "> Loaded via Programmatic Context Calling (Plan A). Citations as [chunk_id].\n"
        )

        output.append("### EVIDENCE (read-only)")

        # Add Skeletons first as navigation
        for chunk in l0_res.chunks:
            output.append(f"#### [{chunk.id}] {chunk.title_path[0]} (Skeleton)")
            output.append(chunk.text)
            output.append("")

        # Add Excerpts
        for chunk in evid_res.chunks:
            output.append(f"#### [{chunk.id}] {' > '.join(chunk.title_path)}")
            output.append(chunk.text)
            output.append("")

        if evid_res.total_tokens > 1500:
            output.append("\n> [!WARNING]")
            output.append("> Context budget reached. Some evidence might be truncated or omitted.")

        return "\n".join(output)

        if evid_res.total_tokens >= 1000:
            output.append("> [!WARNING]")
            output.append("> Context budget reached. Evidence was truncated (Backpressure).")

        return "\n".join(output)

    def _fallback_load(self, target_path: Path, task: str) -> str:
        """Traditional heuristic file selection fallback."""
        task_lower = task.lower()
        ctx_dir = target_path / "_ctx"

        prime_files = list(ctx_dir.glob("prime_*.md"))
        prime_path = prime_files[0] if prime_files else None

        files_to_load = [target_path / "skill.md"]

        # Heuristics
        if any(kw in task_lower for kw in ["implement", "debug", "fix", "code"]):
            files_to_load.append(ctx_dir / "agent.md")

        if any(kw in task_lower for kw in ["plan", "design", "doc"]):
            if prime_path:
                files_to_load.append(prime_path)

        if any(kw in task_lower for kw in ["session", "handoff", "history"]):
            session_files = list(ctx_dir.glob("session_*.md"))
            if session_files:
                files_to_load.append(session_files[0])

        output = [f"# Context (Fallback Heuristic) for Task: {task}\n"]
        for f in files_to_load:
            if f.exists():
                output.append(f"## File: {f.name}")
                output.append(f.read_text())
                output.append("\n---\n")

        return "\n".join(output)


class ValidateContextPackUseCase:
    """Validator for Context Pack integrity and invariants."""

    def __init__(self, file_system: FileSystemAdapter, telemetry: Any = None) -> None:
        self.file_system = file_system
        self.telemetry = telemetry

    def execute(self, target_path: Path) -> ValidationResult:
        """Validate context_pack.json structure and consistency."""
        errors: list[str] = []
        warnings: list[str] = []

        # 0. Path Sanitization
        segment = target_path.name
        if ".." in segment or segment.startswith("/"):
            errors.append(f"Invalid or unsafe segment path: {segment}")
            return ValidationResult(passed=False, errors=errors, warnings=[])

        ctx_dir = target_path / "_ctx"
        pack_path = ctx_dir / "context_pack.json"

        if not pack_path.exists():
            return ValidationResult(passed=False, errors=["Missing context_pack.json"], warnings=[])

        try:
            import json
            import hashlib

            with open(pack_path, "r") as f:
                data = json.load(f)

            # 1. Schema version check
            if data.get("schema_version") != 1:
                errors.append(f"Unsupported schema version: {data.get('schema_version')}")

            # 2. Size limits check
            chunks_data = data.get("chunks", [])
            total_chars = sum(c.get("char_count", 0) for c in chunks_data)
            if total_chars > 2_000_000:  # 2MB limit for context pack (reasonable)
                warnings.append(f"Context pack is quite large ({total_chars} chars)")

            # 3. Index integrity
            chunk_ids = {c["id"] for c in chunks_data}
            for entry in data.get("index", []):
                if entry["id"] not in chunk_ids:
                    errors.append(f"Index references missing chunk ID: {entry['id']}")

            # 4. Source file traceability (SHA256/mtime/chars)
            for src in data.get("source_files", []):
                src_rel_path = src["path"]
                src_abs_path = target_path.parent / src_rel_path

                if not src_abs_path.exists():
                    errors.append(
                        f"Source file listed in pack but missing from disk: {src_rel_path}"
                    )
                    continue

                # Deep verification
                content = src_abs_path.read_bytes()
                current_sha = hashlib.sha256(content).hexdigest()
                current_chars = len(content.decode(errors="ignore"))
                current_mtime = src_abs_path.stat().st_mtime

                if current_sha != src["sha256"]:
                    errors.append(f"Source file content changed (Hash mismatch): {src_rel_path}")
                elif abs(current_mtime - src["mtime"]) > 1.0:  # 1s tolerance
                    warnings.append(f"Source file mtime changed but hash matches: {src_rel_path}")

                if current_chars != src["chars"]:
                    errors.append(
                        f"Source file size mismatch: {src_rel_path} ({current_chars} vs {src['chars']})"
                    )

            # 5. Basic content check
            if not chunks_data:
                errors.append("Context pack contains no chunks")

        except Exception as e:
            errors.append(f"Failed to parse context pack: {str(e)}")

        result = ValidationResult(passed=len(errors) == 0, errors=errors, warnings=warnings)

        # Record result and stale detection
        if self.telemetry:
            if result.passed:
                self.telemetry.incr("ctx_validate_pass_count")
                self.telemetry.stale_detected = False
            else:
                self.telemetry.incr("ctx_validate_fail_count")
                # Check if failure is due to stale/corruption
                is_stale = any("changed" in e.lower() or "mismatch" in e.lower() for e in errors)
                self.telemetry.stale_detected = is_stale

        return result


class AutopilotUseCase:
    """Runner for automated context refresh based on session.md contract."""

    def __init__(self, file_system: FileSystemAdapter):
        self.file_system = file_system

    def execute(self, target_path: Path) -> dict[str, Any]:
        """Read autopilot config and run steps."""
        ctx_dir = target_path / "_ctx"
        session_files = list(ctx_dir.glob("session_*.md"))

        if not session_files:
            return {"status": "skipped", "reason": "No session file found"}

        session_path = session_files[0]
        content = session_path.read_text()

        # Extract YAML frontmatter or block
        try:
            # Simple extractor for YAML block in markdown
            import re

            match = re.search(r"```yaml\n(autopilot:.*?)\n```", content, re.DOTALL)
            if not match:
                # Try frontmatter (---)
                match = re.search(r"^---\n(autopilot:.*?)\n---", content, re.DOTALL | re.MULTILINE)

            if not match:
                return {"status": "skipped", "reason": "No autopilot config found in session.md"}

            config = yaml.safe_load(match.group(1)).get("autopilot", {})
            if not config.get("enabled", False):
                return {"status": "skipped", "reason": "Autopilot disabled in config"}

            steps = config.get("steps", [])
            timeouts = config.get("timeouts", {})
            results = []
            log_entries = [f"--- Autopilot Run: {datetime.now().isoformat()} ---"]

            for step in steps:
                cmd = step.split()
                timeout = timeouts.get(step.replace("trifecta ctx ", ""), 30)

                try:
                    full_cmd = (
                        ["python3", "-m", "src.infrastructure.cli"]
                        + cmd[1:]
                        + ["--path", str(target_path)]
                    )
                    process = subprocess.run(
                        full_cmd, capture_output=True, text=True, timeout=timeout
                    )

                    success = process.returncode == 0
                    results.append(
                        {
                            "step": step,
                            "success": success,
                            "stdout": process.stdout.strip(),
                            "stderr": process.stderr.strip(),
                        }
                    )

                    status_str = "SUCCESS" if success else "FAILED"
                    log_entries.append(f"[{status_str}] {step}")
                    if not success:
                        log_entries.append(f"  Error: {process.stderr.strip()}")
                        break  # Stop on first failure
                except subprocess.TimeoutExpired:
                    results.append({"step": step, "success": False, "error": "Timeout"})
                    log_entries.append(f"[TIMEOUT] {step}")
                    break

            # Write to autopilot.log
            log_path = ctx_dir / "autopilot.log"
            with open(log_path, "a") as f:
                f.write("\n".join(log_entries) + "\n\n")

            return {"status": "completed", "results": results}

        except Exception as e:
            return {"status": "error", "reason": f"Failed to execute autopilot: {str(e)}"}
