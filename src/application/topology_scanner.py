"""Repository topology scanner for Python codebases.

NOTE: module_name is a path-dotted identifier (e.g., "src.domain.user"),
NOT necessarily an importable module name. For importable names, you'd need
to configure module roots (e.g., src-layout projects have root at src/).
"""

import os
from dataclasses import dataclass
from pathlib import Path

from src.application.import_extractor import extract_imports
from src.domain.discovery_models import ImportInfo

# Directories to skip during scanning
SKIP_DIRS = frozenset({"__pycache__", ".venv", "venv", "node_modules", ".git"})

# Warning prefix for syntax errors (from ImportExtractor)
SYNTAX_ERROR_PREFIX = "Syntax error"


@dataclass(frozen=True)
class FileInfo:
    """Information about a single Python file."""

    path: Path  # Relative path from root
    module_name: str  # Path-dotted identifier (e.g., "src.domain.user")
    imports: tuple[ImportInfo, ...]  # Raw imports from ImportExtractor
    line_count: int


@dataclass(frozen=True)
class PackageInfo:
    """Information about a Python package (directory with __init__.py)."""

    path: Path  # Relative path from root
    package_name: str  # Path-dotted package name (empty string for root)


@dataclass(frozen=True)
class TopologyMap:
    """Complete topology of a Python repository."""

    root: Path  # Absolute root path
    files: tuple[FileInfo, ...]  # Sorted by path
    packages: tuple[PackageInfo, ...]  # Sorted by path
    scan_errors: tuple[str, ...]  # "path: error_type: message" format


def _should_skip(name: str) -> bool:
    """Check if directory should be skipped during scan."""
    return name in SKIP_DIRS or name.startswith(".")


def _path_to_module(file_path: Path, root: Path) -> str:
    """Convert file path to dotted path identifier.

    Returns empty string for root directory.
    """
    try:
        rel_path = file_path.relative_to(root)
    except ValueError:
        return ""

    parts = list(rel_path.parts)

    # Remove .py extension from filename
    if parts and parts[-1].endswith(".py"):
        parts[-1] = parts[-1].removesuffix(".py")

    # Remove __init__ from package module name
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]

    return ".".join(parts)


def _scan_file(file_path: Path, root: Path) -> tuple[FileInfo, None] | tuple[None, str]:
    """Scan a single Python file.

    Returns:
        (FileInfo, None) on success
        (None, error_message) on failure (includes path and cause)
    """
    rel_path: str | None = None
    try:
        rel_path = str(file_path.relative_to(root))
        source = file_path.read_text(encoding="utf-8", errors="replace")
        result = extract_imports(source)
        # Check for syntax errors in warnings
        for warning in result.warnings:
            if warning.startswith(SYNTAX_ERROR_PREFIX):
                return None, f"{rel_path}: SyntaxError: {warning}"
        return (
            FileInfo(
                path=file_path.relative_to(root),
                module_name=_path_to_module(file_path, root),
                imports=result.imports,
                line_count=result.line_count,
            ),
            None,
        )
    except Exception as e:
        path_str = rel_path or str(file_path)
        return None, f"{path_str}: {type(e).__name__}: {e}"


def scan_topology(root: Path) -> TopologyMap:
    """Recursively scan a directory tree for Python modules and packages.

    Output is deterministic: files and packages are sorted by path.

    Filters out: __pycache__, .venv, venv, node_modules, .git, and any
    directory starting with "."

    Args:
        root: Absolute or relative path to the repository root

    Returns:
        TopologyMap with all discovered files (sorted), packages (sorted),
        and scan errors in "path: error_type: message" format
    """
    root = root.resolve()
    files: list[FileInfo] = []
    packages: list[PackageInfo] = []
    errors: list[str] = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Filter out skipped directories (modifies dirnames in-place)
        dirnames[:] = [d for d in dirnames if not _should_skip(d)]

        # Sort for deterministic iteration order
        dirnames.sort()
        filenames.sort()

        dir_path = Path(dirpath)

        # Check for package
        if "__init__.py" in filenames:
            pkg_name = _path_to_module(dir_path, root)
            packages.append(
                PackageInfo(
                    path=dir_path.relative_to(root),
                    package_name=pkg_name,
                )
            )

        # Scan Python files
        for fname in filenames:
            if fname.endswith(".py"):
                file_path = dir_path / fname
                file_info, error = _scan_file(file_path, root)
                if error:
                    errors.append(error)
                elif file_info:
                    files.append(file_info)

    # Sort output for determinism
    files.sort(key=lambda f: str(f.path))
    packages.sort(key=lambda p: str(p.path))

    return TopologyMap(
        root=root,
        files=tuple(files),
        packages=tuple(packages),
        scan_errors=tuple(errors),
    )
