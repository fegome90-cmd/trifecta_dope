import unittest
from unittest.mock import MagicMock
from pathlib import Path
from src.application.oracle_use_case import SearchOracleUseCase
from src.domain.result import Ok, Err
from src.domain.context_models import SearchResult, SearchHit, OracleResult


class TestSearchOracleUseCase(unittest.TestCase):
    def setUp(self):
        self.ast_builder = MagicMock()
        self.telemetry = MagicMock()
        self.repo_path = Path("/tmp/test_repo")
        
        self.oracle_uc = SearchOracleUseCase(
            self.ast_builder,
            telemetry=self.telemetry
        )

    @unittest.mock.patch('src.application.oracle_use_case.ContextService')
    def test_execute_fallback_mode(self, mock_svc_cls):
        # PRIME results only, no AST file found
        mock_svc = MagicMock()
        mock_svc_cls.return_value = mock_svc
        hit = SearchHit(id="test:1", title_path=["test"], preview="...", token_est=10, source_path="missing.py", score=1.0)
        mock_svc.search.return_value = SearchResult(hits=[hit])
        
        res = self.oracle_uc.execute(self.repo_path, "test query")
        
        self.assertTrue(res.is_ok())
        self.assertEqual(res.unwrap().fidelity, "fallback")
        self.assertEqual(len(res.unwrap().prime_chunks), 1)

    @unittest.mock.patch('src.application.oracle_use_case.ContextService')
    def test_execute_degraded_mode_with_ast(self, mock_svc_cls):
        # PRIME + AST available
        mock_svc = MagicMock()
        mock_svc_cls.return_value = mock_svc
        hit = SearchHit(id="test:1", title_path=["test"], preview="...", token_est=10, source_path="real.py", score=1.0)
        mock_svc.search.return_value = SearchResult(hits=[hit])
        
        # Mock file exists
        with unittest.mock.patch('pathlib.Path.exists', return_value=True):
            with unittest.mock.patch('pathlib.Path.is_file', return_value=True):
                symbol = MagicMock()
                symbol.name = "MyClass"
                ast_symbols_mock = MagicMock()
                ast_symbols_mock.symbols = [symbol]
                self.ast_builder.build.return_value = ast_symbols_mock
                
                res = self.oracle_uc.execute(self.repo_path, "test query")
                
                self.assertTrue(res.is_ok())
                self.assertEqual(res.unwrap().fidelity, "degraded")
                self.assertIn("MyClass", res.unwrap().ast_symbols)

if __name__ == "__main__":
    unittest.main()
