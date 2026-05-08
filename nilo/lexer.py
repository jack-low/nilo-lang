from .errors import LexError
from .token import KEYWORDS, Token, TokenKind


SINGLE = {
    "=": TokenKind.ASSIGN,
    "!": TokenKind.BANG,
    "<": TokenKind.LT,
    ">": TokenKind.GT,
    "+": TokenKind.PLUS,
    "-": TokenKind.MINUS,
    "*": TokenKind.STAR,
    "/": TokenKind.SLASH,
    "%": TokenKind.PERCENT,
    "(": TokenKind.LPAREN,
    ")": TokenKind.RPAREN,
    "{": TokenKind.LBRACE,
    "}": TokenKind.RBRACE,
    "[": TokenKind.LBRACKET,
    "]": TokenKind.RBRACKET,
    ",": TokenKind.COMMA,
    ".": TokenKind.DOT,
    ":": TokenKind.COLON,
    ";": TokenKind.SEMICOLON,
}

DOUBLE = {
    "->": TokenKind.ARROW,
    "==": TokenKind.EQEQ,
    "!=": TokenKind.BANGEQ,
    "<=": TokenKind.LTE,
    ">=": TokenKind.GTE,
    "&&": TokenKind.ANDAND,
    "||": TokenKind.OROR,
}


class Lexer:
    def __init__(self, source: str, filename: str = "<source>"):
        self.source = source
        self.filename = filename
        self.i = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> list[Token]:
        tokens = []
        while not self._at_end():
            ch = self._peek()
            if ch in " \t\r":
                self._advance()
            elif ch == "\n":
                self._newline()
            elif ch == "/" and self._peek_next() == "/":
                self._comment()
            elif ch == '"':
                tokens.append(self._string())
            elif ch.isdigit():
                tokens.append(self._number())
            elif ch.isalpha() or ch == "_":
                tokens.append(self._identifier())
            else:
                tokens.append(self._symbol())
        tokens.append(Token(TokenKind.EOF, None, self.line, self.column))
        return tokens

    def _symbol(self) -> Token:
        line, column = self.line, self.column
        two = self.source[self.i : self.i + 2]
        if two in DOUBLE:
            self._advance()
            self._advance()
            return Token(DOUBLE[two], two, line, column)
        ch = self._advance()
        if ch in SINGLE:
            return Token(SINGLE[ch], ch, line, column)
        raise LexError(f"{self.filename}:{line}:{column}: unexpected character {ch!r}")

    def _string(self) -> Token:
        line, column = self.line, self.column
        self._advance()
        out = []
        while not self._at_end() and self._peek() != '"':
            ch = self._advance()
            if ch == "\\":
                esc = self._advance()
                out.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(esc, esc))
            else:
                out.append(ch)
        if self._at_end():
            raise LexError(f"{self.filename}:{line}:{column}: unterminated string")
        self._advance()
        return Token(TokenKind.STRING, "".join(out), line, column)

    def _number(self) -> Token:
        line, column = self.line, self.column
        start = self.i
        while not self._at_end() and self._peek().isdigit():
            self._advance()
        if not self._at_end() and self._peek() == "." and self._peek_next().isdigit():
            self._advance()
            while not self._at_end() and self._peek().isdigit():
                self._advance()
            return Token(TokenKind.FLOAT, float(self.source[start:self.i]), line, column)
        return Token(TokenKind.INT, int(self.source[start:self.i]), line, column)

    def _identifier(self) -> Token:
        line, column = self.line, self.column
        start = self.i
        while not self._at_end() and (self._peek().isalnum() or self._peek() == "_"):
            self._advance()
        text = self.source[start:self.i]
        return Token(KEYWORDS.get(text, TokenKind.IDENT), text, line, column)

    def _comment(self) -> None:
        while not self._at_end() and self._peek() != "\n":
            self._advance()

    def _peek(self) -> str:
        return self.source[self.i]

    def _peek_next(self) -> str:
        return "\0" if self.i + 1 >= len(self.source) else self.source[self.i + 1]

    def _advance(self) -> str:
        ch = self.source[self.i]
        self.i += 1
        self.column += 1
        return ch

    def _newline(self) -> None:
        self.i += 1
        self.line += 1
        self.column = 1

    def _at_end(self) -> bool:
        return self.i >= len(self.source)
