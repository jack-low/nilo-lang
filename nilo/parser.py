from . import ast
from .errors import ParseError
from .token import Token, TokenKind as K


class Parser:
    def __init__(self, tokens: list[Token], filename: str = "<source>"):
        self.tokens = tokens
        self.filename = filename
        self.i = 0

    def parse(self) -> ast.Program:
        statements = []
        while not self._check(K.EOF):
            statements.append(self._declaration())
        return ast.Program(statements)

    def _declaration(self):
        exported = self._match(K.EXPORT)
        if self._match(K.IMPORT):
            if exported:
                self._error(self._previous(), "import cannot be exported")
            return self._import_stmt()
        if self._match(K.FROM):
            if exported:
                self._error(self._previous(), "from import cannot be exported")
            return self._from_import_stmt()
        if self._match(K.LET):
            return self._let_stmt(exported)
        if self._match(K.FUNC):
            return self._func_decl(exported)
        if self._match(K.TYPE):
            return self._type_decl(exported)
        if exported:
            self._error(self._previous(), "export must be followed by let, func, or type")
        return self._statement()

    def _import_stmt(self):
        path = self._consume(K.STRING, "expected module path string").value
        alias = None
        if self._match(K.AS):
            alias = self._consume(K.IDENT, "expected import alias").value
        self._consume(K.SEMICOLON, "expected ';' after import")
        return ast.Import(path, alias)

    def _from_import_stmt(self):
        path = self._consume(K.STRING, "expected module path string").value
        self._consume(K.IMPORT, "expected import")
        names = [self._consume(K.IDENT, "expected imported name").value]
        while self._match(K.COMMA):
            names.append(self._consume(K.IDENT, "expected imported name").value)
        self._consume(K.SEMICOLON, "expected ';' after import")
        return ast.FromImport(path, names)

    def _let_stmt(self, exported=False):
        name = self._consume(K.IDENT, "expected variable name").value
        if self._match(K.COLON):
            self._type_name()
        self._consume(K.ASSIGN, "expected '=' in let declaration")
        value = self._expression()
        self._consume(K.SEMICOLON, "expected ';' after declaration")
        return ast.Let(name, value, exported)

    def _func_decl(self, exported=False):
        name = self._consume(K.IDENT, "expected function name").value
        self._consume(K.LPAREN, "expected '(' after function name")
        params = []
        if not self._check(K.RPAREN):
            while True:
                param = self._consume(K.IDENT, "expected parameter name").value
                param_type = None
                if self._match(K.COLON):
                    param_type = self._type_name()
                params.append((param, param_type))
                if not self._match(K.COMMA):
                    break
        self._consume(K.RPAREN, "expected ')' after parameters")
        return_type = None
        if self._match(K.ARROW):
            return_type = self._type_name()
        body = self._block()
        return ast.Func(name, params, return_type, body, exported)

    def _type_decl(self, exported=False):
        name = self._consume(K.IDENT, "expected type name").value
        self._consume(K.LBRACE, "expected '{' after type name")
        fields = []
        while not self._check(K.RBRACE):
            field = self._consume(K.IDENT, "expected field name").value
            field_type = None
            if self._match(K.COLON):
                field_type = self._type_name()
            fields.append((field, field_type))
            self._match(K.COMMA) or self._match(K.SEMICOLON)
        self._consume(K.RBRACE, "expected '}' after type fields")
        return ast.TypeDecl(name, fields, exported)

    def _statement(self):
        if self._match(K.RETURN):
            value = self._expression()
            self._consume(K.SEMICOLON, "expected ';' after return")
            return ast.Return(value)
        if self._match(K.IF):
            self._consume(K.LPAREN, "expected '(' after if")
            condition = self._expression()
            self._consume(K.RPAREN, "expected ')' after if condition")
            then_block = self._block()
            else_block = self._block() if self._match(K.ELSE) else None
            return ast.If(condition, then_block, else_block)
        if self._match(K.WHILE):
            self._consume(K.LPAREN, "expected '(' after while")
            condition = self._expression()
            self._consume(K.RPAREN, "expected ')' after while condition")
            return ast.While(condition, self._block())
        if self._match(K.FOR):
            name = self._consume(K.IDENT, "expected loop variable after for").value
            self._consume(K.IN, "expected 'in' after loop variable")
            iterable = self._expression()
            return ast.For(name, iterable, self._block())
        if self._check(K.IDENT) and self._peek_next().kind == K.ASSIGN:
            name = self._advance().value
            self._advance()
            value = self._expression()
            self._consume(K.SEMICOLON, "expected ';' after assignment")
            return ast.Assign(name, value)
        expr = self._expression()
        self._consume(K.SEMICOLON, "expected ';' after expression")
        return ast.ExprStmt(expr)

    def _block(self):
        self._consume(K.LBRACE, "expected '{'")
        statements = []
        while not self._check(K.RBRACE):
            if self._check(K.EOF):
                self._error(self._peek(), "unterminated block")
            statements.append(self._declaration())
        self._consume(K.RBRACE, "expected '}'")
        return ast.Block(statements)

    def _expression(self):
        return self._or()

    def _or(self):
        expr = self._and()
        while self._match(K.OROR):
            expr = ast.Binary(expr, "||", self._and())
        return expr

    def _and(self):
        expr = self._equality()
        while self._match(K.ANDAND):
            expr = ast.Binary(expr, "&&", self._equality())
        return expr

    def _equality(self):
        expr = self._comparison()
        while self._match(K.EQEQ, K.BANGEQ):
            expr = ast.Binary(expr, self._previous().value, self._comparison())
        return expr

    def _comparison(self):
        expr = self._term()
        while self._match(K.LT, K.LTE, K.GT, K.GTE):
            expr = ast.Binary(expr, self._previous().value, self._term())
        return expr

    def _term(self):
        expr = self._factor()
        while self._match(K.PLUS, K.MINUS):
            expr = ast.Binary(expr, self._previous().value, self._factor())
        return expr

    def _factor(self):
        expr = self._unary()
        while self._match(K.STAR, K.SLASH, K.PERCENT):
            expr = ast.Binary(expr, self._previous().value, self._unary())
        return expr

    def _unary(self):
        if self._match(K.BANG, K.MINUS):
            return ast.Unary(self._previous().value, self._unary())
        return self._postfix()

    def _postfix(self):
        expr = self._primary()
        while True:
            if self._match(K.LPAREN):
                args = []
                if not self._check(K.RPAREN):
                    while True:
                        args.append(self._expression())
                        if not self._match(K.COMMA):
                            break
                self._consume(K.RPAREN, "expected ')' after arguments")
                expr = ast.Call(expr, args)
            elif self._match(K.DOT):
                expr = ast.Get(expr, self._consume(K.IDENT, "expected property name").value)
            elif self._match(K.LBRACKET):
                index = self._expression()
                self._consume(K.RBRACKET, "expected ']' after index")
                expr = ast.Index(expr, index)
            else:
                break
        return expr

    def _primary(self):
        if self._match(K.INT, K.FLOAT, K.STRING):
            return ast.Literal(self._previous().value)
        if self._match(K.TRUE):
            return ast.Literal(True)
        if self._match(K.FALSE):
            return ast.Literal(False)
        if self._match(K.NIL):
            return ast.Literal(None)
        if self._match(K.IDENT):
            return ast.Var(self._previous().value)
        if self._match(K.LBRACKET):
            values = []
            if not self._check(K.RBRACKET):
                while True:
                    values.append(self._expression())
                    if not self._match(K.COMMA):
                        break
            self._consume(K.RBRACKET, "expected ']' after list")
            return ast.ListExpr(values)
        if self._match(K.LBRACE):
            entries = []
            if not self._check(K.RBRACE):
                while True:
                    key = self._expression()
                    self._consume(K.COLON, "expected ':' between map key and value")
                    value = self._expression()
                    entries.append((key, value))
                    if not self._match(K.COMMA):
                        break
            self._consume(K.RBRACE, "expected '}' after map")
            return ast.MapExpr(entries)
        if self._match(K.LPAREN):
            expr = self._expression()
            self._consume(K.RPAREN, "expected ')' after expression")
            return expr
        self._error(self._peek(), "expected expression")

    def _type_name(self) -> str:
        return self._consume(K.IDENT, "expected type name").value

    def _match(self, *kinds) -> bool:
        if self._check(*kinds):
            self._advance()
            return True
        return False

    def _consume(self, kind, message):
        if self._check(kind):
            return self._advance()
        self._error(self._peek(), message)

    def _check(self, *kinds) -> bool:
        return self._peek().kind in kinds

    def _advance(self) -> Token:
        token = self._peek()
        self.i += 1
        return token

    def _peek(self) -> Token:
        return self.tokens[self.i]

    def _peek_next(self) -> Token:
        return self.tokens[min(self.i + 1, len(self.tokens) - 1)]

    def _previous(self) -> Token:
        return self.tokens[self.i - 1]

    def _error(self, token: Token, message: str):
        raise ParseError(f"{self.filename}:{token.line}:{token.column}: {message}")
