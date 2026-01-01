from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Range(BaseModel):
    start_line: int
    end_line: int


class ASTError(BaseModel):
    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class ChildSymbol(BaseModel):
    name: str
    kind: str
    range: Range
    signature_stub: Optional[str] = None


class ASTData(BaseModel):
    uri: str
    range: Optional[Range] = None
    content: Optional[str] = None
    children: List[ChildSymbol] = Field(default_factory=list)
    truncated: bool = False
    truncated_reason: Optional[str] = None


class ASTRef(BaseModel):
    file: str
    line: int
    text: str


class ASTResponse(BaseModel):
    status: str
    kind: str = "skeleton"  # skeleton | snippet
    data: Optional[ASTData] = None
    refs: List[ASTRef] = Field(default_factory=list)
    errors: List[ASTError] = Field(default_factory=list)
    next_actions: List[str] = Field(default_factory=list)


class ASTErrorCode:
    INTERNAL_ERROR = "INTERNAL_ERROR"
    AMBIGUOUS_SYMBOL = "AMBIGUOUS_SYMBOL"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    SYMBOL_NOT_FOUND = "SYMBOL_NOT_FOUND"
    INVALID_URI = "INVALID_URI"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
