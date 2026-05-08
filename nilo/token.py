from dataclasses import dataclass
from enum import Enum, auto


class TokenKind(Enum):
    EOF = auto()
    IDENT = auto()
    INT = auto()
    FLOAT = auto()
    STRING = auto()
    TRUE = auto()
    FALSE = auto()
    NIL = auto()
    LET = auto()
    FUNC = auto()
    RETURN = auto()
    TYPE = auto()
    IMPORT = auto()
    FROM = auto()
    AS = auto()
    EXPORT = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    IN = auto()
    ARROW = auto()
    EQEQ = auto()
    BANGEQ = auto()
    LTE = auto()
    GTE = auto()
    ANDAND = auto()
    OROR = auto()
    ASSIGN = auto()
    BANG = auto()
    LT = auto()
    GT = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    DOT = auto()
    COLON = auto()
    SEMICOLON = auto()


KEYWORDS = {
    "let": TokenKind.LET,
    "func": TokenKind.FUNC,
    "return": TokenKind.RETURN,
    "type": TokenKind.TYPE,
    "import": TokenKind.IMPORT,
    "from": TokenKind.FROM,
    "as": TokenKind.AS,
    "export": TokenKind.EXPORT,
    "if": TokenKind.IF,
    "else": TokenKind.ELSE,
    "while": TokenKind.WHILE,
    "for": TokenKind.FOR,
    "in": TokenKind.IN,
    "true": TokenKind.TRUE,
    "false": TokenKind.FALSE,
    "nil": TokenKind.NIL,
}


@dataclass(frozen=True)
class Token:
    kind: TokenKind
    value: object
    line: int
    column: int
