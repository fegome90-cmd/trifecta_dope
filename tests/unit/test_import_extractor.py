"""Tests for import_extractor module."""

from src.application.import_extractor import extract_imports


class TestExtractImports:
    """Test extract_imports function."""

    def test_simple_import(self):
        source = "import os"
        result = extract_imports(source)
        assert len(result.imports) == 1
        imp = result.imports[0]
        assert imp.name == "os"
        assert imp.is_relative is False
        assert imp.level == 0
        assert imp.imported_names == ()

    def test_from_import(self):
        source = "from os import path"
        result = extract_imports(source)
        assert len(result.imports) == 1
        imp = result.imports[0]
        assert imp.name == "os"
        assert imp.imported_names == ("path",)

    def test_multiple_imports(self):
        source = "from os import path, getcwd"
        result = extract_imports(source)
        assert len(result.imports) == 1
        assert result.imports[0].imported_names == ("path", "getcwd")

    def test_relative_import(self):
        source = "from . import module"
        result = extract_imports(source)
        assert len(result.imports) == 1
        imp = result.imports[0]
        assert imp.is_relative is True
        assert imp.level == 1

    def test_relative_import_nested(self):
        source = "from .. import something"
        result = extract_imports(source)
        assert len(result.imports) == 1
        assert result.imports[0].level == 2

    def test_wildcard_import(self):
        source = "from os import *"
        result = extract_imports(source)
        assert len(result.imports) == 1
        assert result.imports[0].is_wildcard is True

    def test_multiple_import_statements(self):
        source = """import os
import sys
from collections import OrderedDict"""
        result = extract_imports(source)
        assert len(result.imports) == 3

    def test_dynamic_import_warning(self):
        source = "x = __import__('os')"
        result = extract_imports(source)
        assert len(result.imports) == 0
        assert len(result.warnings) > 0

    def test_empty_source(self):
        source = ""
        result = extract_imports(source)
        assert len(result.imports) == 0

    def test_no_imports(self):
        source = "def foo():\n    return 1"
        result = extract_imports(source)
        assert len(result.imports) == 0
