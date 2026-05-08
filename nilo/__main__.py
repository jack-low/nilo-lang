import argparse
from dataclasses import asdict, is_dataclass
import json
from pathlib import Path
import sys

from .errors import NiloError
from .diagnostics import format_error
from .runtime import parse_source, run_file, run_source, tokenize_source


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="nilo", description="Run and manage Nilo programs.")
    sub = parser.add_subparsers(dest="command")

    run_cmd = sub.add_parser("run", help="run a Nilo source file")
    run_cmd.add_argument("run_file")

    eval_cmd = sub.add_parser("eval", help="run source passed on the command line")
    eval_cmd.add_argument("source")

    test_cmd = sub.add_parser("test", help="run Nilo test files")
    test_cmd.add_argument("path", nargs="?", default="tests")

    init_cmd = sub.add_parser("init", help="create a new Nilo project")
    init_cmd.add_argument("path", nargs="?", default=".")

    tokens_cmd = sub.add_parser("tokens", help="print lexer tokens")
    tokens_cmd.add_argument("tokens_file")

    ast_cmd = sub.add_parser("ast", help="print parsed AST as JSON")
    ast_cmd.add_argument("ast_file")

    parser.add_argument("file", nargs="?", help=argparse.SUPPRESS)
    parser.add_argument("-e", "--eval", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    try:
        if args.eval is not None:
            run_source(args.eval)
        elif args.command == "run":
            run_file(args.run_file)
        elif args.command == "eval":
            run_source(args.source)
        elif args.command == "test":
            return run_tests(Path(args.path))
        elif args.command == "init":
            init_project(Path(args.path))
        elif args.command == "tokens":
            print_tokens(Path(args.tokens_file))
        elif args.command == "ast":
            print_ast(Path(args.ast_file))
        elif args.file:
            run_file(args.file)
        else:
            repl()
        return 0
    except NiloError as exc:
        print(format_error(exc), file=sys.stderr)
        return 1


def run_tests(path: Path) -> int:
    files = [path] if path.is_file() else sorted(path.glob("**/*_test.nilo"))
    if not files:
        print(f"no Nilo tests found in {path}")
        return 1
    failed = 0
    for file in files:
        try:
            run_file(file)
            print(f"ok {file}")
        except NiloError as exc:
            failed += 1
            print(f"fail {file}: {exc}", file=sys.stderr)
    print(f"{len(files) - failed} passed, {failed} failed")
    return 1 if failed else 0


def init_project(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "src").mkdir(exist_ok=True)
    (path / "tests").mkdir(exist_ok=True)
    write_if_missing(
        path / "Nilo.toml",
        """[package]
name = "my-nilo-app"
version = "0.1.0"
entry = "src/main.nilo"

[exports]
main = "src/main.nilo"
""",
    )
    write_if_missing(path / "src" / "main.nilo", 'print("Hello from Nilo");\n')
    write_if_missing(path / "tests" / "main_test.nilo", 'print("test ok");\n')
    print(f"initialized Nilo project at {path.resolve()}")


def write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def print_tokens(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    for token in tokenize_source(source, str(path)):
        print(f"{token.line}:{token.column} {token.kind.name} {token.value!r}")


def print_ast(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    program = parse_source(source, str(path))
    print(json.dumps(to_json(program), indent=2))


def to_json(value):
    if is_dataclass(value):
        data = asdict(value)
        data["node"] = value.__class__.__name__
        return {key: to_json(item) for key, item in data.items()}
    if isinstance(value, list):
        return [to_json(item) for item in value]
    if isinstance(value, tuple):
        return [to_json(item) for item in value]
    if isinstance(value, dict):
        return {str(key): to_json(item) for key, item in value.items()}
    return value


def repl() -> None:
    print("Nilo REPL. Ctrl-D to exit.")
    while True:
        try:
            line = input("nilo> ")
        except EOFError:
            print()
            return
        if not line.strip():
            continue
        run_source(line if line.rstrip().endswith(";") else line + ";")


if __name__ == "__main__":
    raise SystemExit(main())
