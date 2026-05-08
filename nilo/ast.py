from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Program:
    statements: list[Any]


@dataclass(frozen=True)
class Block:
    statements: list[Any]


@dataclass(frozen=True)
class Let:
    name: str
    value: Any
    exported: bool = False


@dataclass(frozen=True)
class Assign:
    name: str
    value: Any


@dataclass(frozen=True)
class Func:
    name: str
    params: list[tuple[str, str | None]]
    return_type: str | None
    body: Block
    exported: bool = False


@dataclass(frozen=True)
class TypeDecl:
    name: str
    fields: list[tuple[str, str | None]]
    exported: bool = False


@dataclass(frozen=True)
class Import:
    path: str
    alias: str | None


@dataclass(frozen=True)
class FromImport:
    path: str
    names: list[str]


@dataclass(frozen=True)
class Return:
    value: Any


@dataclass(frozen=True)
class If:
    condition: Any
    then_block: Block
    else_block: Block | None


@dataclass(frozen=True)
class While:
    condition: Any
    body: Block


@dataclass(frozen=True)
class For:
    name: str
    iterable: Any
    body: Block


@dataclass(frozen=True)
class ExprStmt:
    expr: Any


@dataclass(frozen=True)
class Literal:
    value: Any


@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class ListExpr:
    values: list[Any]


@dataclass(frozen=True)
class MapExpr:
    entries: list[tuple[Any, Any]]


@dataclass(frozen=True)
class Unary:
    op: str
    right: Any


@dataclass(frozen=True)
class Binary:
    left: Any
    op: str
    right: Any


@dataclass(frozen=True)
class Call:
    callee: Any
    args: list[Any]


@dataclass(frozen=True)
class Get:
    target: Any
    name: str


@dataclass(frozen=True)
class Index:
    target: Any
    index: Any
