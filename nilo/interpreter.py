from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import time
from typing import Any, Callable
from urllib import error, request

from . import ast
from .errors import RuntimeError


class ReturnSignal(Exception):
    def __init__(self, value: Any):
        self.value = value


class Env:
    def __init__(self, parent: Env | None = None):
        self.parent = parent
        self.values: dict[str, Any] = {}

    def define(self, name: str, value: Any) -> None:
        self.values[name] = value

    def assign(self, name: str, value: Any) -> None:
        if name in self.values:
            self.values[name] = value
            return
        if self.parent:
            self.parent.assign(name, value)
            return
        raise RuntimeError(f"undefined variable '{name}'")

    def get(self, name: str) -> Any:
        if name in self.values:
            return self.values[name]
        if self.parent:
            return self.parent.get(name)
        raise RuntimeError(f"undefined variable '{name}'")


@dataclass
class Module:
    path: Path
    exports: dict[str, Any]


@dataclass
class UserFunction:
    name: str
    params: list[tuple[str, str | None]]
    body: ast.Block
    closure: Env

    def call(self, interpreter: Interpreter, args: list[Any]) -> Any:
        if len(args) != len(self.params):
            raise RuntimeError(f"{self.name} expected {len(self.params)} args, got {len(args)}")
        env = Env(self.closure)
        for (name, _), value in zip(self.params, args):
            env.define(name, value)
        try:
            interpreter.execute_block(self.body.statements, env)
        except ReturnSignal as signal:
            return signal.value
        return None


@dataclass
class BuiltinFunction:
    name: str
    fn: Callable[[list[Any]], Any]
    arity: int | None = None

    def call(self, _interpreter: Interpreter, args: list[Any]) -> Any:
        if self.arity is not None and len(args) != self.arity:
            raise RuntimeError(f"{self.name} expected {self.arity} args, got {len(args)}")
        return self.fn(args)


class StructType:
    def __init__(self, name: str, fields: list[tuple[str, str | None]]):
        self.name = name
        self.fields = [field for field, _ in fields]

    def call(self, _interpreter: Interpreter, args: list[Any]) -> dict[str, Any]:
        if len(args) != len(self.fields):
            raise RuntimeError(f"{self.name} expected {len(self.fields)} fields, got {len(args)}")
        return {"__type__": self.name, **dict(zip(self.fields, args))}

    def __repr__(self) -> str:
        return f"<type {self.name}>"


class RegexPattern:
    def __init__(self, pattern: str, flags: int = 0):
        self.pattern = pattern
        self.flags = flags
        try:
            self.compiled = re.compile(pattern, flags)
        except re.error as exc:
            raise RuntimeError(f"invalid regex pattern: {exc}") from exc

    def call(self, _interpreter: Interpreter, args: list[Any]) -> Any:
        if len(args) != 1:
            raise RuntimeError(f"regex pattern expected 1 arg, got {len(args)}")
        return self.match(args[0]) is not None

    def match(self, text: Any):
        return self.compiled.search(str(text))

    def __repr__(self) -> str:
        return f"<regex {self.pattern!r}>"


class Interpreter:
    def __init__(self, root: Path | None = None):
        self.root = (root or Path.cwd()).resolve()
        self.modules: dict[Path, Module] = {}
        self.globals = Env()
        self._install_builtins(self.globals)

    def interpret(self, program: ast.Program, filename: str = "<source>") -> dict[str, Any]:
        exports: dict[str, Any] = {}
        env = self.globals
        for stmt in program.statements:
            self.execute(stmt, env, exports, Path(filename))
        return exports

    def execute_block(self, statements: list[Any], env: Env) -> None:
        for stmt in statements:
            self.execute(stmt, env, {}, self.root / "<block>")

    def execute(self, stmt: Any, env: Env, exports: dict[str, Any], filename: Path) -> None:
        if isinstance(stmt, ast.Let):
            value = self.eval(stmt.value, env)
            env.define(stmt.name, value)
            if stmt.exported:
                exports[stmt.name] = value
        elif isinstance(stmt, ast.Assign):
            env.assign(stmt.name, self.eval(stmt.value, env))
        elif isinstance(stmt, ast.Func):
            fn = UserFunction(stmt.name, stmt.params, stmt.body, env)
            env.define(stmt.name, fn)
            if stmt.exported:
                exports[stmt.name] = fn
        elif isinstance(stmt, ast.TypeDecl):
            typ = StructType(stmt.name, stmt.fields)
            env.define(stmt.name, typ)
            if stmt.exported:
                exports[stmt.name] = typ
        elif isinstance(stmt, ast.Import):
            module = self.load_module(stmt.path, filename)
            name = stmt.alias or self._module_name(stmt.path)
            env.define(name, module.exports)
        elif isinstance(stmt, ast.FromImport):
            module = self.load_module(stmt.path, filename)
            for name in stmt.names:
                if name not in module.exports:
                    raise RuntimeError(f"module '{stmt.path}' does not export '{name}'")
                env.define(name, module.exports[name])
        elif isinstance(stmt, ast.Return):
            raise ReturnSignal(self.eval(stmt.value, env))
        elif isinstance(stmt, ast.If):
            if self._truthy(self.eval(stmt.condition, env)):
                self.execute_block(stmt.then_block.statements, Env(env))
            elif stmt.else_block:
                self.execute_block(stmt.else_block.statements, Env(env))
        elif isinstance(stmt, ast.While):
            while self._truthy(self.eval(stmt.condition, env)):
                self.execute_block(stmt.body.statements, Env(env))
        elif isinstance(stmt, ast.For):
            iterable = self.eval(stmt.iterable, env)
            for value in iterable:
                loop_env = Env(env)
                loop_env.define(stmt.name, value)
                self.execute_block(stmt.body.statements, loop_env)
        elif isinstance(stmt, ast.ExprStmt):
            self.eval(stmt.expr, env)
        else:
            raise RuntimeError(f"unsupported statement {stmt!r}")

    def eval(self, expr: Any, env: Env) -> Any:
        if isinstance(expr, ast.Literal):
            return expr.value
        if isinstance(expr, ast.Var):
            return env.get(expr.name)
        if isinstance(expr, ast.ListExpr):
            return [self.eval(value, env) for value in expr.values]
        if isinstance(expr, ast.MapExpr):
            return {self.eval(key, env): self.eval(value, env) for key, value in expr.entries}
        if isinstance(expr, ast.Unary):
            right = self.eval(expr.right, env)
            if expr.op == "-":
                return -right
            if expr.op == "!":
                return not self._truthy(right)
        if isinstance(expr, ast.Binary):
            if expr.op == "&&":
                return self._truthy(self.eval(expr.left, env)) and self._truthy(self.eval(expr.right, env))
            if expr.op == "||":
                return self._truthy(self.eval(expr.left, env)) or self._truthy(self.eval(expr.right, env))
            left = self.eval(expr.left, env)
            right = self.eval(expr.right, env)
            return self._binary(expr.op, left, right)
        if isinstance(expr, ast.Call):
            callee = self.eval(expr.callee, env)
            args = [self.eval(arg, env) for arg in expr.args]
            if not hasattr(callee, "call"):
                raise RuntimeError(f"{callee!r} is not callable")
            return callee.call(self, args)
        if isinstance(expr, ast.Get):
            target = self.eval(expr.target, env)
            if isinstance(target, dict) and expr.name in target:
                return target[expr.name]
            raise RuntimeError(f"property '{expr.name}' not found")
        if isinstance(expr, ast.Index):
            target = self.eval(expr.target, env)
            index = self.eval(expr.index, env)
            return target[index]
        raise RuntimeError(f"unsupported expression {expr!r}")

    def load_module(self, path_text: str, importer: Path) -> Module:
        if path_text.startswith("std/"):
            return self.load_std_module(path_text)

        path = Path(path_text)
        if not path.is_absolute():
            base = importer.parent if importer.name != "<source>" else self.root
            path = base / path
        if path.suffix == "":
            path = path.with_suffix(".nilo")
        path = path.resolve()
        if path in self.modules:
            return self.modules[path]
        from .runtime import parse_source

        if not path.exists():
            raise RuntimeError(f"module not found: {path}")
        module = Module(path, {})
        self.modules[path] = module
        source = path.read_text(encoding="utf-8")
        program = parse_source(source, str(path))
        module_env = Env(self.globals)
        exports: dict[str, Any] = {}
        for stmt in program.statements:
            self.execute(stmt, module_env, exports, path)
        module.exports = exports
        return module

    def load_std_module(self, path_text: str) -> Module:
        path = Path(f"<{path_text}>")
        if path in self.modules:
            return self.modules[path]
        exports = self._std_exports(path_text)
        module = Module(path, exports)
        self.modules[path] = module
        return module

    def _std_exports(self, path_text: str) -> dict[str, Any]:
        modules = {
            "std/json": {
                "parse": BuiltinFunction("json.parse", lambda args: json.loads(args[0]), 1),
                "stringify": BuiltinFunction("json.stringify", lambda args: json.dumps(args[0]), 1),
            },
            "std/regex": {
                "compile": BuiltinFunction("regex.compile", self._regex_compile, None),
                "is_match": BuiltinFunction("regex.is_match", self._regex_is_match, None),
                "find": BuiltinFunction("regex.find", self._regex_find, None),
                "find_all": BuiltinFunction("regex.find_all", self._regex_find_all, None),
                "captures": BuiltinFunction("regex.captures", self._regex_captures, None),
                "replace": BuiltinFunction("regex.replace", self._regex_replace, None),
                "split": BuiltinFunction("regex.split", self._regex_split, None),
                "escape": BuiltinFunction("regex.escape", lambda args: re.escape(str(args[0])), 1),
                "flags": {
                    "ignore_case": re.IGNORECASE,
                    "multiline": re.MULTILINE,
                    "dot_all": re.DOTALL,
                    "verbose": re.VERBOSE,
                    "ascii": re.ASCII,
                },
            },
            "std/fs": {
                "read_text": BuiltinFunction("fs.read_text", lambda args: Path(args[0]).read_text(encoding="utf-8"), 1),
                "write_text": BuiltinFunction("fs.write_text", self._fs_write_text, 2),
                "exists": BuiltinFunction("fs.exists", lambda args: Path(args[0]).exists(), 1),
            },
            "std/time": {
                "now": BuiltinFunction("time.now", lambda args: time.time(), 0),
                "sleep": BuiltinFunction("time.sleep", lambda args: time.sleep(args[0]) or None, 1),
            },
            "std/http": {
                "get": BuiltinFunction("http.get", lambda args: self._http_request("GET", args), None),
                "post": BuiltinFunction("http.post", lambda args: self._http_request("POST", args), None),
            },
            "std/list": {
                "push": BuiltinFunction("list.push", self._push, 2),
                "join": BuiltinFunction("list.join", lambda args: str(args[1]).join(map(str, args[0])), 2),
            },
            "std/string": {
                "split": BuiltinFunction("string.split", lambda args: str(args[0]).split(args[1]), 2),
                "trim": BuiltinFunction("string.trim", lambda args: str(args[0]).strip(), 1),
                "lower": BuiltinFunction("string.lower", lambda args: str(args[0]).lower(), 1),
                "upper": BuiltinFunction("string.upper", lambda args: str(args[0]).upper(), 1),
            },
            "std/math": {
                "abs": BuiltinFunction("math.abs", lambda args: abs(args[0]), 1),
                "min": BuiltinFunction("math.min", lambda args: min(args), None),
                "max": BuiltinFunction("math.max", lambda args: max(args), None),
            },
        }
        if path_text not in modules:
            raise RuntimeError(f"standard module not found: {path_text}")
        return modules[path_text]

    def _install_builtins(self, env: Env) -> None:
        env.define("print", BuiltinFunction("print", lambda args: print(*args) or None))
        env.define("len", BuiltinFunction("len", lambda args: len(args[0]), 1))
        env.define("push", BuiltinFunction("push", self._push, 2))
        env.define("str", BuiltinFunction("str", lambda args: str(args[0]), 1))
        env.define("int", BuiltinFunction("int", lambda args: int(args[0]), 1))
        env.define("float", BuiltinFunction("float", lambda args: float(args[0]), 1))
        env.define("range", BuiltinFunction("range", lambda args: list(range(*args))))

    def _push(self, args: list[Any]) -> Any:
        args[0].append(args[1])
        return args[0]

    def _fs_write_text(self, args: list[Any]) -> Any:
        Path(args[0]).write_text(str(args[1]), encoding="utf-8")
        return None

    def _regex_compile(self, args: list[Any]) -> RegexPattern:
        if not 1 <= len(args) <= 2:
            raise RuntimeError(f"regex.compile expected 1 or 2 args, got {len(args)}")
        return RegexPattern(str(args[0]), self._regex_flags(args[1] if len(args) == 2 else 0))

    def _regex_is_match(self, args: list[Any]) -> bool:
        if not 2 <= len(args) <= 3:
            raise RuntimeError(f"regex.is_match expected 2 or 3 args, got {len(args)}")
        return self._regex(args[0], args[2] if len(args) == 3 else 0).match(args[1]) is not None

    def _regex_find(self, args: list[Any]) -> dict[str, Any] | None:
        if not 2 <= len(args) <= 3:
            raise RuntimeError(f"regex.find expected 2 or 3 args, got {len(args)}")
        match = self._regex(args[0], args[2] if len(args) == 3 else 0).match(args[1])
        return self._regex_match(match) if match else None

    def _regex_find_all(self, args: list[Any]) -> list[dict[str, Any]]:
        if not 2 <= len(args) <= 3:
            raise RuntimeError(f"regex.find_all expected 2 or 3 args, got {len(args)}")
        pattern = self._regex(args[0], args[2] if len(args) == 3 else 0)
        return [self._regex_match(match) for match in pattern.compiled.finditer(str(args[1]))]

    def _regex_captures(self, args: list[Any]) -> dict[str, Any] | None:
        if not 2 <= len(args) <= 3:
            raise RuntimeError(f"regex.captures expected 2 or 3 args, got {len(args)}")
        match = self._regex(args[0], args[2] if len(args) == 3 else 0).match(args[1])
        if not match:
            return None
        return {
            "match": match.group(0),
            "groups": list(match.groups()),
            "named": match.groupdict(),
        }

    def _regex_replace(self, args: list[Any]) -> str:
        if not 3 <= len(args) <= 4:
            raise RuntimeError(f"regex.replace expected 3 or 4 args, got {len(args)}")
        pattern = self._regex(args[0], args[3] if len(args) == 4 else 0)
        return pattern.compiled.sub(str(args[2]), str(args[1]))

    def _regex_split(self, args: list[Any]) -> list[str]:
        if not 2 <= len(args) <= 3:
            raise RuntimeError(f"regex.split expected 2 or 3 args, got {len(args)}")
        pattern = self._regex(args[0], args[2] if len(args) == 3 else 0)
        return pattern.compiled.split(str(args[1]))

    def _regex(self, pattern: Any, flags: Any = 0) -> RegexPattern:
        if isinstance(pattern, RegexPattern):
            return pattern
        return RegexPattern(str(pattern), self._regex_flags(flags))

    def _regex_flags(self, flags: Any) -> int:
        if flags is None:
            return 0
        if isinstance(flags, list):
            value = 0
            for flag in flags:
                value |= int(flag)
            return value
        return int(flags)

    def _regex_match(self, match: re.Match) -> dict[str, Any]:
        return {
            "text": match.group(0),
            "start": match.start(),
            "end": match.end(),
            "groups": list(match.groups()),
            "named": match.groupdict(),
        }

    def _http_request(self, method: str, args: list[Any]) -> dict[str, Any]:
        if not args:
            raise RuntimeError(f"http.{method.lower()} expected at least 1 arg")
        url = args[0]
        body = None
        headers = {}
        if len(args) >= 2 and args[1] is not None:
            body = str(args[1]).encode("utf-8")
        if len(args) >= 3 and args[2] is not None:
            headers = dict(args[2])
        req = request.Request(url, data=body, headers=headers, method=method)
        try:
            with request.urlopen(req, timeout=15) as response:
                return {
                    "status": response.status,
                    "headers": dict(response.headers),
                    "body": response.read().decode("utf-8"),
                }
        except error.HTTPError as exc:
            return {
                "status": exc.code,
                "headers": dict(exc.headers),
                "body": exc.read().decode("utf-8"),
            }

    def _binary(self, op: str, left: Any, right: Any) -> Any:
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/":
            return left / right
        if op == "%":
            return left % right
        if op == "==":
            return left == right
        if op == "!=":
            return left != right
        if op == "<":
            return left < right
        if op == "<=":
            return left <= right
        if op == ">":
            return left > right
        if op == ">=":
            return left >= right
        raise RuntimeError(f"unknown operator '{op}'")

    def _truthy(self, value: Any) -> bool:
        return bool(value)

    def _module_name(self, path: str) -> str:
        return Path(path).stem.replace("-", "_")
