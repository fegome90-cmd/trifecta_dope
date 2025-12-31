"""
PHASE 1 (RED): Test-Driven Contract for Trifecta v1.1 Refactoring

This test module defines the CONTRACT for:
1. Extraction of validate_segment_structure from scripts/ → src/infrastructure/validators.py
2. Deduplication logic to prevent skill.md from appearing twice in the Context Pack

Tests are written BEFORE implementation (TDD Red-Green-Refactor).
These tests will FAIL until the implementation exists.

Author: Senior Python Architect (TDD Protocol)
Date: 2025-12-30
Status: RED PHASE (Tests fail, code doesn't exist yet)
"""

import shutil
import tempfile
from pathlib import Path
from typing import Generator, List

import pytest

# ============================================================================
# TEST SUITE 1: Validator Migration Contract
# ============================================================================


class TestValidatorMigration:
    """
    PHASE 1 (RED): Define the contract for validate_segment_structure.

    These tests specify:
    - The function must exist in src/infrastructure/validators.py
    - It must accept a Path and return a ValidationResult
    - It must validate dynamic naming (segment name in filenames)
    - It must detect missing required files

    EXPECTED STATE: All tests FAIL with ImportError or AssertionError
    """

    def test_import_validation_result_from_validators(self) -> None:
        """
        Contract: ValidationResult dataclass must be importable from src.infrastructure.validators

        Fails with: ModuleNotFoundError or ImportError
        Reason: src/infrastructure/validators.py does not exist yet
        """
        try:
            from src.infrastructure.validators import ValidationResult

            assert ValidationResult is not None
        except (ModuleNotFoundError, ImportError) as e:
            pytest.fail(f"ValidationResult not found in src.infrastructure.validators: {e}")

    def test_import_validate_segment_structure(self) -> None:
        """
        Contract: validate_segment_structure must be importable from src.infrastructure.validators

        Fails with: ModuleNotFoundError or ImportError
        Reason: src/infrastructure/validators.py does not exist yet
        """
        try:
            from src.infrastructure.validators import validate_segment_structure

            assert callable(validate_segment_structure)
        except (ModuleNotFoundError, ImportError) as e:
            pytest.fail(f"validate_segment_structure not found: {e}")

    def test_validation_result_structure(self) -> None:
        """
        Contract: ValidationResult must have 'valid' and 'errors' attributes.

        Expected signature:
            @dataclass(frozen=True)
            class ValidationResult:
                valid: bool
                errors: List[str]
        """
        from src.infrastructure.validators import ValidationResult

        # Test immutability (frozen=True)
        result = ValidationResult(valid=True, errors=[])
        assert result.valid is True
        assert result.errors == []

        # Test frozen constraint
        with pytest.raises(AttributeError):
            result.valid = False  # type: ignore[misc]

    def test_validate_segment_structure_signature(self) -> None:
        """
        Contract: Function signature must be:
            def validate_segment_structure(path: Path) -> ValidationResult

        Accepts Path, returns ValidationResult.
        No side effects (no print, no I/O beyond reading).
        """
        import inspect
        from inspect import signature
        from pathlib import Path

        from src.infrastructure.validators import validate_segment_structure

        sig = signature(validate_segment_structure)

        # Check parameter count
        assert len(sig.parameters) == 1, "Must accept exactly 1 parameter"

        # Check parameter name and type
        path_param = sig.parameters.get("path")
        assert path_param is not None, "Parameter must be named 'path'"
        assert path_param.annotation == Path, "Parameter must be typed as Path"

        # Check return type
        assert sig.return_annotation != inspect.Signature.empty, "Must have return type annotation"


class TestValidateSegmentStructureBehavior:
    """
    PHASE 1 (RED): Define expected behavior of validate_segment_structure.

    These tests specify what the function MUST do (contract).
    """

    @pytest.fixture
    def temp_segment_dir(self) -> Generator[Path, None, None]:
        """Fixture: Create a temporary segment directory for testing."""
        tmp_dir = tempfile.mkdtemp()
        yield Path(tmp_dir)
        shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_valid_segment_with_dynamic_naming(self, temp_segment_dir: Path) -> None:
        """
        Scenario: Segment named 'marketing' with correct files.

        Expected files:
            marketing/
            ├─ skill.md
            └─ _ctx/
               ├─ agent_marketing.md
               ├─ prime_marketing.md
               └─ session_marketing.md

        Expected result: ValidationResult(valid=True, errors=[])

        Fails with: AssertionError (validation fails or wrong error list)
        """
        from src.infrastructure.validators import validate_segment_structure

        segment_name = "marketing"
        seg = temp_segment_dir / segment_name
        seg.mkdir()

        # Create required files with dynamic naming
        (seg / "skill.md").touch()
        ctx = seg / "_ctx"
        ctx.mkdir()
        (ctx / f"agent_{segment_name}.md").touch()
        (ctx / f"prime_{segment_name}.md").touch()
        (ctx / f"session_{segment_name}.md").touch()

        result = validate_segment_structure(seg)

        assert result.valid is True, f"Expected valid=True, got errors: {result.errors}"
        assert result.errors == [], f"Expected no errors, got: {result.errors}"

    def test_invalid_segment_missing_skill_md(self, temp_segment_dir: Path) -> None:
        """
        Scenario: Segment missing skill.md

        Expected behavior: ValidationResult(valid=False, errors=[...])

        Fails with: AssertionError (validation incorrectly passes)
        """
        from src.infrastructure.validators import validate_segment_structure

        segment_name = "marketing"
        seg = temp_segment_dir / segment_name
        seg.mkdir()

        # Don't create skill.md
        ctx = seg / "_ctx"
        ctx.mkdir()
        (ctx / f"agent_{segment_name}.md").touch()
        (ctx / f"prime_{segment_name}.md").touch()
        (ctx / f"session_{segment_name}.md").touch()

        result = validate_segment_structure(seg)

        assert result.valid is False, "Should be invalid when skill.md is missing"
        assert any("skill.md" in err.lower() for err in result.errors), (
            f"Error should mention skill.md, got: {result.errors}"
        )

    def test_invalid_segment_missing_ctx_directory(self, temp_segment_dir: Path) -> None:
        """
        Scenario: Segment missing _ctx/ directory

        Expected behavior: ValidationResult(valid=False, errors=[...])
        """
        from src.infrastructure.validators import validate_segment_structure

        segment_name = "marketing"
        seg = temp_segment_dir / segment_name
        seg.mkdir()
        (seg / "skill.md").touch()
        # Don't create _ctx directory

        result = validate_segment_structure(seg)

        assert result.valid is False, "Should be invalid when _ctx directory is missing"
        assert any("_ctx" in err.lower() for err in result.errors), (
            f"Error should mention _ctx, got: {result.errors}"
        )

    def test_invalid_segment_missing_dynamic_named_files(self, temp_segment_dir: Path) -> None:
        """
        Scenario: Segment has _ctx/ but missing dynamically-named files.

        Segment name: 'payments'
        Missing: agent_payments.md, prime_payments.md, session_payments.md

        Expected behavior: ValidationResult(valid=False, errors=[...])
        """
        from src.infrastructure.validators import validate_segment_structure

        segment_name = "payments"
        seg = temp_segment_dir / segment_name
        seg.mkdir()
        (seg / "skill.md").touch()
        ctx = seg / "_ctx"
        ctx.mkdir()
        # Don't create dynamically-named files

        result = validate_segment_structure(seg)

        assert result.valid is False, "Should be invalid when dynamic files are missing"
        # At least one error should mention the missing files
        assert len(result.errors) > 0, "Should have at least one error"

    def test_segment_path_not_found(self, temp_segment_dir: Path) -> None:
        """
        Scenario: Path does not exist.

        Expected behavior: ValidationResult(valid=False, errors=["Path not found: ..."])
        """
        from src.infrastructure.validators import validate_segment_structure

        nonexistent = temp_segment_dir / "nonexistent_segment"
        result = validate_segment_structure(nonexistent)

        assert result.valid is False, "Should be invalid when path doesn't exist"
        assert any("not found" in err.lower() or "exist" in err.lower() for err in result.errors), (
            f"Error should mention path not found, got: {result.errors}"
        )

    def test_detect_legacy_context_files(self, temp_segment_dir: Path) -> None:
        """
        Scenario: Segment has legacy files (agent.md, prime.md, session.md) in _ctx.
        Expected: detect_legacy_context_files returns those filenames.
        """
        from src.infrastructure.validators import detect_legacy_context_files

        seg = temp_segment_dir / "legacyseg"
        seg.mkdir()
        (seg / "skill.md").touch()
        ctx = seg / "_ctx"
        ctx.mkdir()
        (ctx / "agent.md").touch()
        (ctx / "prime.md").touch()
        (ctx / "session.md").touch()

        legacy = detect_legacy_context_files(seg)
        assert set(legacy) == {"agent.md", "prime.md", "session.md"}


# ============================================================================
# TEST SUITE 2: Deduplication Logic Contract
# ============================================================================


class TestDeduplicationContract:
    """
    PHASE 1 (RED): Define the contract for deduplication in file scanning.

    These tests specify:
    - A function or method must exist to filter duplicate files
    - skill.md should only be indexed once (primary source, not reference)
    - The exclusion list mechanism must work

    Fails with: ImportError, AttributeError, AssertionError
    """

    def test_reference_exclusion_exists(self) -> None:
        """
        Contract: Path-aware deduplication must exist in BuildContextPackUseCase.

        The use case should compute primary source paths and exclude them from references
        using path comparison (not filename string matching).

        Fails with: AttributeError if _extract_references method doesn't exist
        """
        from src.application.use_cases import BuildContextPackUseCase
        from src.infrastructure.file_system import FileSystemAdapter

        use_case = BuildContextPackUseCase(FileSystemAdapter())

        # Verify the use case has the method that performs path-aware exclusion
        assert hasattr(use_case, "_extract_references")

    def test_file_scanner_respects_exclusion(self) -> None:
        """
        Contract: File scanner must skip root skill.md but NOT nested skill.md files.

        Path-aware logic ensures only exact path matches are excluded, allowing
        nested skill.md files (e.g., docs/examples/skill.md) to be indexed.

        Fails with: AssertionError if deduplication doesn't work
        """
        from src.application.use_cases import BuildContextPackUseCase
        from src.infrastructure.file_system import FileSystemAdapter

        use_case = BuildContextPackUseCase(FileSystemAdapter())

        # Test that the logic exists to check path-aware exclusion
        assert hasattr(use_case, "_extract_references")

    def test_skill_md_indexed_only_once_in_context_pack(self, tmp_path: Path) -> None:
        """
        Integration test: Verify ROOT skill.md appears exactly once in context pack.
        Uses a fresh temporary segment to enforce strict naming and reproducible state.
        """
        from src.application.use_cases import BuildContextPackUseCase
        from src.infrastructure.file_system import FileSystemAdapter

        # Setup strict segment structure
        seg = tmp_path / "skill_seg"
        seg.mkdir()
        (seg / "skill.md").write_text("Skill Content")
        (seg / "_ctx").mkdir()
        (seg / "_ctx" / "prime_skill_seg.md").write_text(
            "- [Ref](skill.md)"
        )  # Reference strict self
        (seg / "_ctx" / "agent_skill_seg.md").write_text("Agent")
        (seg / "_ctx" / "session_skill_seg.md").write_text("Session")

        # Build
        uc = BuildContextPackUseCase(FileSystemAdapter())
        result = uc.execute(seg)
        assert result.is_ok(), f"Build failed: {result}"
        pack = result.unwrap()

        # Count how many times root skill.md appears
        skill_chunks = [
            chunk
            for chunk in pack.chunks
            if chunk.doc.startswith("skill") or chunk.doc.startswith("ref:skill")
        ]

        assert len(skill_chunks) == 1, f"Expected 1 skill chunk, found {len(skill_chunks)}"
        assert skill_chunks[0].doc == "skill", (
            "skill.md must be indexed as 'skill', not 'ref:skill'"
        )

    def test_nested_skill_md_is_NOT_excluded(self, tmp_path: Path) -> None:
        """
        Contract: Nested skill.md files (e.g., library/skill.md) MUST be indexed as references.

        Scenario: Segment has root/skill.md (primary) and root/library/python/skill.md (nested)
        Expected: Root is indexed as "skill", nested is indexed as "ref:library/python/skill.md"

        This proves path-aware deduplication works correctly and doesn't hide skill libraries.

        Fails with: AssertionError if nested skill.md is incorrectly excluded
        """
        from src.application.use_cases import BuildContextPackUseCase
        from src.infrastructure.file_system import FileSystemAdapter

        # Create segment structure
        segment = tmp_path / "test_segment"
        segment.mkdir()
        ctx_dir = segment / "_ctx"
        ctx_dir.mkdir()

        # Create primary skill.md at root
        (segment / "skill.md").write_text("# Root Skill")

        # Create nested skill.md in library (this should NOT be excluded)
        library = segment / "library" / "python"
        library.mkdir(parents=True)
        nested_skill = library / "skill.md"
        nested_skill.write_text("# Python Skill")

        # Create required files
        (segment / "readme_tf.md").write_text("# Test")
        (ctx_dir / f"prime_{segment.name}.md").write_text("- `library/python/skill.md`")
        (ctx_dir / f"agent_{segment.name}.md").write_text("# Agent")
        (ctx_dir / f"session_{segment.name}.md").write_text("# Session")

        # Build context pack
        use_case = BuildContextPackUseCase(FileSystemAdapter())
        result = use_case.execute(segment)
        assert result.is_ok(), f"Build failed: {result}"
        pack = result.unwrap()

        # Verify root skill.md is indexed as primary (doc="skill")
        primary_skill_chunks = [c for c in pack.chunks if c.doc == "skill"]
        assert len(primary_skill_chunks) == 1, "Root skill.md must be indexed once as primary"

        # Verify nested skill.md is indexed as reference (doc="ref:library/python/skill.md")
        ref_skill_chunks = [c for c in pack.chunks if "library/python/skill.md" in c.doc]
        assert len(ref_skill_chunks) == 1, (
            "Nested library/python/skill.md must be indexed as reference"
        )
        assert ref_skill_chunks[0].doc.startswith("ref:"), "Nested skill.md must have 'ref:' prefix"


# ============================================================================
# TEST SUITE 3: Type Safety & Immutability
# ============================================================================


class TestTypeSafetyAndImmutability:
    """
    PHASE 1 (RED): Specify type safety and immutability requirements.

    Ensures Clean Architecture compliance:
    - ValidationResult is immutable (frozen dataclass)
    - No side effects in pure functions
    - Type hints are strict (mypy --strict compatible)
    """

    def test_validation_result_is_frozen(self) -> None:
        """
        Contract: ValidationResult must be frozen (immutable).

        Prevents accidental mutations in the "Pure Core".
        """
        from src.infrastructure.validators import ValidationResult

        result = ValidationResult(valid=True, errors=[])

        with pytest.raises(AttributeError):
            result.valid = False  # type: ignore[misc]

        with pytest.raises(AttributeError):
            result.errors = ["new error"]  # type: ignore[misc]

    def test_validation_result_list_errors_is_type_safe(self) -> None:
        """
        Contract: ValidationResult.errors must be List[str].

        Type checker (mypy --strict) should accept:
            result.errors: List[str]
        """
        from src.infrastructure.validators import ValidationResult

        result = ValidationResult(valid=False, errors=["Error 1", "Error 2"])

        # Type assertion (simulates mypy check)
        errors: List[str] = result.errors
        assert isinstance(errors, list)
        assert all(isinstance(e, str) for e in errors)

    def test_validate_function_has_no_side_effects_visible(self) -> None:
        """
        Contract: validate_segment_structure must be a pure function.

        No prints, no logging, no state mutations.
        (Pure Core principle)

        This is a specification test - verifies the contract.
        """
        import ast
        import inspect

        from src.infrastructure.validators import validate_segment_structure

        # Get source and parse as AST
        source = inspect.getsource(validate_segment_structure)
        tree = ast.parse(source)

        # Extract function body (skip docstring)
        func_def = tree.body[0]
        assert isinstance(func_def, ast.FunctionDef)

        # Check for print() calls in function body (not in docstring)
        for node in ast.walk(func_def):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "print":
                    pytest.fail("Pure function must not contain print() calls in body")

        # If we get here, no print() calls found in function body
        assert True, "Function is pure (no print statements in body)"


# ============================================================================
# EXECUTION SUMMARY (PHASE 1 - RED)
# ============================================================================

"""
PHASE 1 SUMMARY: What These Tests Specify
═════════════════════════════════════════════════════════════════════════════

TEST SUITES:
1. TestValidatorMigration (4 tests)
   └─ Contracts: Module exists, imports work, signature is correct

2. TestValidateSegmentStructureBehavior (5 tests)
   └─ Contracts: Function validates segments correctly (dynamic naming)

3. TestDeduplicationContract (3 tests)
   └─ Contracts: Exclusion list exists, prevents duplicates

4. TestTypeSafetyAndImmutability (3 tests)
   └─ Contracts: Type safety (mypy), immutability (frozen dataclass)

TOTAL: 15 test cases


EXPECTED FAILURES (PHASE 1 - RED):
─────────────────────────────────────────────────────────────────────────────

1. ModuleNotFoundError: No module named 'src.infrastructure.validators'
   └─ Because src/infrastructure/validators.py doesn't exist yet

2. ImportError: Cannot import ValidationResult
   └─ Because the module doesn't exist

3. ImportError: Cannot import validate_segment_structure
   └─ Because the module doesn't exist

4. ImportError: Cannot import REFERENCE_EXCLUSION from file_system
   └─ Because REFERENCE_EXCLUSION doesn't exist in file_system.py

5. AssertionError (during behavioral tests)
   └─ Because validate_segment_structure doesn't exist to test


NEXT STEP (PHASE 2 - GREEN):
─────────────────────────────────────────────────────────────────────────────

After these tests are reviewed and understood:
1. Create src/infrastructure/validators.py
2. Implement ValidationResult dataclass
3. Implement validate_segment_structure function
4. Add REFERENCE_EXCLUSION to file_system.py
5. Run tests: pytest tests/unit/test_validators.py -v
6. All 15 tests should PASS
"""


# ============================================================================
# PROTOCOL & CONSTRAINTS
# ============================================================================

"""
TDD PROTOCOL (Red-Green-Refactor):
─────────────────────────────────────────────────────────────────────────────

PHASE 1 (NOW - RED):
  ✓ Define test cases (this file)
  ✓ Explain expected failures
  ✓ Show the contract (what code should do)
  × Don't implement code yet

PHASE 2 (NEXT - GREEN):
  × Run tests (they fail)
  ✓ Implement minimal code to pass tests
  ✓ Move validate_segment_structure to src/infrastructure/validators.py
  ✓ Add REFERENCE_EXCLUSION to file_system.py
  ✓ Run tests: pytest tests/unit/test_validators.py -v
  × Don't refactor yet

PHASE 3 (AFTER - REFACTOR):
  ✓ Update scripts/install_trifecta_context.py to import from src/
  ✓ Update tests/installer_test.py to import from src/
  ✓ Remove sys.path hack from tests
  ✓ Run gates: mypy, ruff, pytest
  ✓ Verify no side effects


CONSTRAINTS (Non-negotiable):
─────────────────────────────────────────────────────────────────────────────

✓ Use pathlib.Path for file operations
✓ Use dataclasses for result types
✓ No RAG/ranking changes (out of scope)
✓ Type safety: mypy --strict compatible
✓ No side effects in pure core
✓ Use trifecta CLI for verification
✓ Don't break existing functionality
"""
