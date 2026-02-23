"""Unit tests for topology_scanner module."""

from pathlib import Path

import pytest

from src.application.topology_scanner import FileInfo, PackageInfo, TopologyMap, scan_topology


class TestScanTopologyEmpty:
    """Tests for scanning empty directories."""

    def test_empty_directory_returns_empty_map(self, tmp_path: Path) -> None:
        """Empty directory should return empty TopologyMap."""
        result = scan_topology(tmp_path)

        assert result.files == ()
        assert result.packages == ()
        assert result.scan_errors == ()
        assert result.root == tmp_path.resolve()


class TestScanTopologySingleFile:
    """Tests for scanning directories with single files."""

    def test_single_file_no_package(self, tmp_path: Path) -> None:
        """Single Python file without package should be detected."""
        (tmp_path / "main.py").write_text("import os\nprint('hello')")

        result = scan_topology(tmp_path)

        assert len(result.files) == 1
        assert result.files[0].module_name == "main"
        assert result.files[0].imports[0].name == "os"
        assert result.files[0].line_count == 2
        assert result.packages == ()

    def test_single_file_with_multiple_imports(self, tmp_path: Path) -> None:
        """File with multiple imports should capture all."""
        (tmp_path / "app.py").write_text(
            "import os\nfrom pathlib import Path\nfrom typing import List, Dict\n"
        )

        result = scan_topology(tmp_path)

        assert len(result.files) == 1
        assert len(result.files[0].imports) == 3
        assert result.files[0].imports[0].name == "os"
        assert result.files[0].imports[1].name == "pathlib"
        assert result.files[0].imports[2].imported_names == ("List", "Dict")


class TestScanTopologyPackages:
    """Tests for package detection."""

    def test_single_package_with_init(self, tmp_path: Path) -> None:
        """Directory with __init__.py should be detected as package."""
        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")

        result = scan_topology(tmp_path)

        assert len(result.packages) == 1
        assert result.packages[0].package_name == "mypkg"

    def test_package_with_modules(self, tmp_path: Path) -> None:
        """Package with modules should detect both package and files."""
        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "module.py").write_text("import sys")

        result = scan_topology(tmp_path)

        assert len(result.packages) == 1
        assert len(result.files) == 2  # __init__.py and module.py
        module_file = next(f for f in result.files if f.module_name == "mypkg.module")
        assert module_file.imports[0].name == "sys"


class TestScanTopologyNestedPackages:
    """Tests for nested package structures."""

    def test_nested_packages(self, tmp_path: Path) -> None:
        """Nested packages should have correct dotted names."""
        pkg = tmp_path / "mypkg"
        subpkg = pkg / "subpkg"
        subpkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("")
        (subpkg / "__init__.py").write_text("")
        (subpkg / "module.py").write_text("from pathlib import Path")

        result = scan_topology(tmp_path)

        assert len(result.packages) == 2
        package_names = {p.package_name for p in result.packages}
        assert "mypkg" in package_names
        assert "mypkg.subpkg" in package_names

        module_file = next(
            f for f in result.files if f.module_name == "mypkg.subpkg.module"
        )
        assert module_file.imports[0].name == "pathlib"


class TestScanTopologySkipPatterns:
    """Tests for directory/file skip patterns."""

    def test_skips_pycache(self, tmp_path: Path) -> None:
        """__pycache__ directories should be skipped."""
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "test.pyc").write_text("")
        (tmp_path / "main.py").write_text("pass")

        result = scan_topology(tmp_path)

        assert len(result.files) == 1
        assert result.files[0].module_name == "main"

    def test_skips_venv(self, tmp_path: Path) -> None:
        """.venv directories should be skipped."""
        venv = tmp_path / ".venv"
        venv.mkdir()
        (venv / "lib").mkdir()
        (venv / "lib" / "site.py").write_text("# venv file")
        (tmp_path / "app.py").write_text("pass")

        result = scan_topology(tmp_path)

        assert len(result.files) == 1
        assert result.files[0].module_name == "app"

    def test_skips_venv_no_dot(self, tmp_path: Path) -> None:
        """venv directories (no dot) should be skipped."""
        venv = tmp_path / "venv"
        venv.mkdir()
        (venv / "lib").mkdir()
        (venv / "lib" / "site.py").write_text("# venv file")
        (tmp_path / "app.py").write_text("pass")

        result = scan_topology(tmp_path)

        assert len(result.files) == 1

    def test_skips_node_modules(self, tmp_path: Path) -> None:
        """node_modules directories should be skipped."""
        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        (node_modules / "package").mkdir()
        (tmp_path / "main.py").write_text("pass")

        result = scan_topology(tmp_path)

        assert len(result.files) == 1

    def test_skips_git(self, tmp_path: Path) -> None:
        """.git directories should be skipped."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("")
        (tmp_path / "main.py").write_text("pass")

        result = scan_topology(tmp_path)

        assert len(result.files) == 1


class TestScanTopologyErrors:
    """Tests for error handling."""

    def test_syntax_error_records_in_scan_errors(self, tmp_path: Path) -> None:
        """Files with syntax errors should be recorded in scan_errors with cause."""
        (tmp_path / "broken.py").write_text("def broken(\n")  # Invalid syntax

        result = scan_topology(tmp_path)

        assert len(result.scan_errors) == 1
        assert "broken.py" in result.scan_errors[0]
        assert "SyntaxError" in result.scan_errors[0]
        assert len(result.files) == 0

    def test_multiple_errors_all_recorded(self, tmp_path: Path) -> None:
        """Multiple files with errors should all be recorded."""
        (tmp_path / "broken1.py").write_text("def broken(\n")
        (tmp_path / "broken2.py").write_text("class Foo\n")

        result = scan_topology(tmp_path)

        assert len(result.scan_errors) == 2
        # Each error should include the path and error type
        for err in result.scan_errors:
            assert ".py:" in err  # Format: "path: error_type: message"


class TestFileInfo:
    """Tests for FileInfo dataclass."""

    def test_fileinfo_is_frozen(self, tmp_path: Path) -> None:
        """FileInfo should be immutable (frozen dataclass)."""
        info = FileInfo(
            path=Path("test.py"),
            module_name="test",
            imports=(),
            line_count=10,
        )

        with pytest.raises(AttributeError):
            info.line_count = 20  # type: ignore[misc]


class TestPackageInfo:
    """Tests for PackageInfo dataclass."""

    def test_packageinfo_is_frozen(self) -> None:
        """PackageInfo should be immutable (frozen dataclass)."""
        info = PackageInfo(
            path=Path("mypkg"),
            package_name="mypkg",
        )

        with pytest.raises(AttributeError):
            info.package_name = "other"  # type: ignore[misc]


class TestTopologyMap:
    """Tests for TopologyMap dataclass."""

    def test_topologymap_is_frozen(self, tmp_path: Path) -> None:
        """TopologyMap should be immutable (frozen dataclass)."""
        topo = TopologyMap(
            root=tmp_path,
            files=(),
            packages=(),
            scan_errors=(),
        )

        with pytest.raises(AttributeError):
            topo.files = ()  # type: ignore[misc]

    def test_topologymap_with_data(self, tmp_path: Path) -> None:
        """TopologyMap should hold all scan results."""
        file_info = FileInfo(
            path=Path("main.py"),
            module_name="main",
            imports=(),
            line_count=5,
        )
        pkg_info = PackageInfo(
            path=Path("pkg"),
            package_name="pkg",
        )

        topo = TopologyMap(
            root=tmp_path,
            files=(file_info,),
            packages=(pkg_info,),
            scan_errors=("error1: ErrorType: message",),
        )

        assert len(topo.files) == 1
        assert len(topo.packages) == 1
        assert len(topo.scan_errors) == 1
