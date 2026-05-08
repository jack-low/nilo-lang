from pathlib import Path

from .interpreter import Interpreter
from .lexer import Lexer
from .parser import Parser


def tokenize_source(source: str, filename: str = "<source>"):
    return Lexer(source, filename).tokenize()


def parse_source(source: str, filename: str = "<source>"):
    tokens = tokenize_source(source, filename)
    return Parser(tokens, filename).parse()


def run_source(source: str, filename: str = "<source>", root: str | Path | None = None):
    program = parse_source(source, filename)
    return Interpreter(Path(root).resolve() if root else None).interpret(program, filename)


def run_file(path: str | Path):
    path = Path(path).resolve()
    source = path.read_text(encoding="utf-8")
    program = parse_source(source, str(path))
    return Interpreter(path.parent).interpret(program, str(path))
