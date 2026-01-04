from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Any
from src.domain.result import Result, Ok, Err
from src.domain.ast_models import ASTError, ASTErrorCode
from src.application.ast_parser import SkeletonMapBuilder


@dataclass
class SymbolResolveResult:
    """Result of symbol resolution."""

    resolved: bool = False
    ambiguous: bool = False
    file: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    matches: int = 0
    candidates: List[Any] = field(default_factory=list)


class SymbolQuery:
    def __init__(self, kind: str, path: str, member: Optional[str] = None):
        self.kind = kind
        self.path = path
        self.member = member

    @classmethod
    def parse(cls, uri: str) -> Result["SymbolQuery", ASTError]:
        if not uri.startswith("sym://python/"):
            return Err(
                ASTError(code=ASTErrorCode.INVALID_URI, message="URI must start with sym://python/")
            )

        remainder = uri[len("sym://python/") :]
        parts = remainder.split("/", 1)
        if len(parts) != 2:
            return Err(
                ASTError(code=ASTErrorCode.INVALID_URI, message="URI must contain kind and path")
            )

        kind = parts[0]
        path_member = parts[1]

        if kind not in ("mod", "type"):
            return Err(ASTError(code=ASTErrorCode.INVALID_URI, message="Kind must be mod or type"))

        member = None
        if "#" in path_member:
            path_only, member = path_member.split("#", 1)
        else:
            path_only = path_member

        if kind == "mod" and member:
            return Err(
                ASTError(
                    code=ASTErrorCode.INVALID_URI, message="Kind 'mod' should not have fragment"
                )
            )

        return Ok(cls(kind, path_only, member))


class Candidate:
    def __init__(
        self,
        file_rel: str,
        kind: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
    ):
        self.file_rel = file_rel
        self.kind = kind
        self.start_line = start_line
        self.end_line = end_line


class SymbolResolver:
    def __init__(self, builder: Any, root: Optional[Path] = None):
        self.builder = builder
        self.root = root or Path.cwd()

    def resolve(self, query: SymbolQuery) -> Result[Candidate, ASTError]:
        # Simple resolution logic
        # 1. Exact file
        candidate_file = self.root / f"{query.path}.py"
        candidate_init = self.root / query.path / "__init__.py"

        file_exists = candidate_file.exists() and candidate_file.is_file()
        init_exists = candidate_init.exists() and candidate_init.is_file()

        if file_exists and init_exists:
            return Err(
                ASTError(code=ASTErrorCode.AMBIGUOUS_SYMBOL, message="Ambiguous module path")
            )

        if file_exists:
            return Ok(Candidate(f"{query.path}.py", "mod"))
        elif init_exists:
            return Ok(Candidate(f"{query.path}/__init__.py", "mod"))

        # If member is present, we might be looking for a type in a file
        # But for strictly restoring what works:
        return Err(
            ASTError(
                code=ASTErrorCode.FILE_NOT_FOUND, message=f"Could not find module for {query.path}"
            )
        )
