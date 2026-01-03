"""
Unit tests for Symbol Selector DSL (v0).
Focus: Strict regex, path splitting, fail-closed logic.
"""

from src.application.symbol_selector import SymbolQuery
from src.domain.ast_models import ASTErrorCode
from src.domain.result import Err, Ok


class TestSymbolQuery:
    def test_parse_valid_mod(self):
        """Valid sym://python/mod/..."""
        res = SymbolQuery.parse("sym://python/mod/pkg/utils")
        assert isinstance(res, Ok)
        q = res.value
        assert q.kind == "mod"
        assert q.path == "pkg/utils"
        assert q.member is None

    def test_parse_valid_type(self):
        """Valid sym://python/type/..."""
        res = SymbolQuery.parse("sym://python/type/pkg/user/User")
        assert isinstance(res, Ok)
        q = res.value
        assert q.kind == "type"
        assert q.path == "pkg/user/User"
        assert q.member is None

    def test_parse_valid_type_with_member(self):
        """Valid type with #member"""
        res = SymbolQuery.parse("sym://python/type/foo/Bar#baz")
        assert isinstance(res, Ok)
        q = res.value
        assert q.kind == "type"
        assert q.path == "foo/Bar"
        assert q.member == "baz"

    def test_parse_invalid_scheme(self):
        """Invalid scheme -> Error"""
        res = SymbolQuery.parse("http://python/mod/foo")
        assert isinstance(res, Err)
        assert res.error.code == ASTErrorCode.INVALID_URI

    def test_parse_invalid_lang(self):
        """Only python supported"""
        res = SymbolQuery.parse("sym://js/mod/foo")
        assert isinstance(res, Err)

    def test_parse_invalid_kind(self):
        """Kind must be mod or type"""
        res = SymbolQuery.parse("sym://python/func/foo")
        assert isinstance(res, Err)

    def test_parse_mod_with_member(self):
        """Mod cannot have fragment"""
        res = SymbolQuery.parse("sym://python/mod/foo#bar")
        assert isinstance(res, Err)
        assert "Kind 'mod' should not have fragment" in res.error.message


# Integration tests for Resolver with Mock Filesystem will be in test_cli_ast.py
