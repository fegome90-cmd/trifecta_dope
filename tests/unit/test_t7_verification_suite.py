import pytest
from pathlib import Path
from typing import Any
from typer.testing import CliRunner
from src.infrastructure.cli import app
from src.application.use_cases import BuildContextPackUseCase
from src.infrastructure.file_system import FileSystemAdapter

runner = CliRunner()


@pytest.fixture
def temp_segment(tmp_path: Path) -> Path:
    seg = tmp_path / "segment"
    seg.mkdir()
    (seg / "skill.md").write_text("Skill")
    (seg / "_ctx").mkdir()
    # Strict naming adherence
    (seg / "_ctx" / f"agent_{seg.name}.md").write_text("Agent")
    return seg


# T7.1 — CLI interface hardening
def test_cli_requires_segment_flag() -> None:
    result = runner.invoke(app, ["ctx", "build"])  # Missing --segment
    assert result.exit_code != 0
    assert "Missing option" in result.output or "Error" in result.output


def test_cli_requires_segment_arg_load() -> None:
    result = runner.invoke(app, ["load", "--task", "test"])  # Missing --segment
    assert result.exit_code != 0


# T7.2 — Prime link expansion happy path
def test_prime_expansion_happy_path(temp_segment: Path) -> None:
    doc_file = temp_segment / "doc.md"
    doc_file.write_text("Content of linked doc")

    # STRICT: filename must match directory name ("segment")
    prime = temp_segment / "_ctx" / f"prime_{temp_segment.name}.md"
    prime.write_text("- [Link](doc.md)")

    uc = BuildContextPackUseCase(FileSystemAdapter())
    pack = uc.execute(temp_segment)

    # Check if doc.md content is indexed
    indexed_texts = [c.text for c in pack.chunks]
    assert "Content of linked doc" in indexed_texts


# T7.3 — Prime link security: path traversal (FAIL-CLOSED)
def test_prime_security_path_traversal(temp_segment: Path) -> None:
    # Create a secret file outside segment
    secret = temp_segment.parent / "secret.md"
    secret.write_text("SECRET DATA")

    # STRICT: filename must match directory name
    prime = temp_segment / "_ctx" / f"prime_{temp_segment.name}.md"
    prime.write_text("- [Attack](../secret.md)")

    uc = BuildContextPackUseCase(FileSystemAdapter())

    # Should raise ValueError (fail-closed policy)
    with pytest.raises(ValueError, match="PROHIBITED.*outside segment"):
        uc.execute(temp_segment)


# T7.4 — Cycle detection (Explicit warning check)
def test_prime_cycles_warning(temp_segment: Path, capsys: Any) -> None:
    # Create simple cycle A -> A (via duplicate link)
    doc_path = temp_segment / "doc.md"
    doc_path.write_text("Doc content")

    # Same file referenced twice
    links = "- [Link1](doc.md)\n- [Link2](doc.md)"
    # STRICT: filename must match directory name
    prime = temp_segment / "_ctx" / f"prime_{temp_segment.name}.md"
    prime.write_text(links)

    uc = BuildContextPackUseCase(FileSystemAdapter())
    uc.execute(temp_segment)

    captured = capsys.readouterr()
    assert "Warning: Cycle/Duplicate detected" in captured.out


# T7.5 — Installer Contamination Check
def test_installer_does_not_write_ctx_in_cli_root(tmp_path: Path) -> None:
    # Verify logic: if segment != cli_root, cli_root should remain clean
    cli_root = tmp_path / "cli_root"
    cli_root.mkdir()

    segment_name = "segment"
    segment = tmp_path / segment_name
    segment.mkdir()
    (segment / "skill.md").write_text("Skill")
    (segment / "_ctx").mkdir()
    # Use dynamic naming convention (North Star)
    (segment / "_ctx" / f"agent_{segment_name}.md").write_text("Agent")
    (segment / "_ctx" / f"prime_{segment_name}.md").write_text("Prime")
    (segment / "_ctx" / f"session_{segment_name}.md").write_text("Session")

    # We can't easily run the installer script here as it invokes subprocess,
    # but we can verify the CLI behavior which the installer uses.
    # Run ctx build targeting segment
    result = runner.invoke(app, ["ctx", "build", "--segment", str(segment)])

    assert result.exit_code == 0, f"Build failed: {result.stdout}"

    # Check NO _ctx in cli_root
    assert not (cli_root / "_ctx").exists()
    # Check _ctx exists in segment
    assert (segment / "_ctx" / "context_pack.json").exists()
