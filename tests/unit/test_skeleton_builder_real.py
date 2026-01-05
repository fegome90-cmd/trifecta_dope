"""Unit tests for SkeletonMapBuilder with real ast parsing."""

from src.application.ast_parser import SkeletonMapBuilder, ParseResult


def test_skeleton_builder_extracts_function(tmp_path):
    """Should extract function definitions."""
    py_file = tmp_path / "example.py"
    py_file.write_text("def foo():\n    pass\n")

    builder = SkeletonMapBuilder()
    result = builder.build(py_file)

    assert isinstance(result, ParseResult)
    assert len(result.symbols) == 1
    assert result.symbols[0].name == "foo"
    assert result.symbols[0].kind == "function"
    assert result.symbols[0].start_line == 1


def test_skeleton_builder_extracts_class(tmp_path):
    """Should extract class definitions."""
    py_file = tmp_path / "example.py"
    py_file.write_text("class Bar:\n    pass\n")

    builder = SkeletonMapBuilder()
    result = builder.build(py_file)

    assert isinstance(result, ParseResult)
    assert len(result.symbols) == 1
    assert result.symbols[0].name == "Bar"
    assert result.symbols[0].kind == "class"


def test_skeleton_builder_extracts_mixed(tmp_path):
    """Should extract both functions and classes."""
    py_file = tmp_path / "example.py"
    py_file.write_text("def foo():\n    pass\n\nclass Bar:\n    pass\n")

    builder = SkeletonMapBuilder()
    result = builder.build(py_file)

    assert isinstance(result, ParseResult)
    assert len(result.symbols) == 2
    assert result.symbols[0].name == "foo"
    assert result.symbols[1].name == "Bar"
