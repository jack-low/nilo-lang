# Nilo

Nilo is a small programming language project focused on readable syntax, simple modules, and an implementation that is easy to grow.

The current implementation is an alpha interpreter written in Python with no runtime dependencies.

## Features

- Variables with `let`
- Functions and `return`
- Arithmetic, comparisons, booleans, strings, lists, and indexing
- Maps, property access, `if` / `else`, `while`, and `for ... in`
- Lightweight record-style `type` declarations
- File modules with `export`, `import`, and `from ... import ...`
- Standard modules such as `std/json`, `std/fs`, `std/http`, `std/time`
- CLI runner, REPL, project init, test runner, token dump, and AST dump

## Quick Start

```bash
python3 -m nilo examples/main.nilo
```

Or after installing locally:

```bash
python3 -m pip install -e .
nilo examples/main.nilo
```

The explicit command form is:

```bash
python3 -m nilo run examples/main.nilo
python3 -m nilo test
python3 -m nilo init my-app
python3 -m nilo tokens examples/main.nilo
python3 -m nilo ast examples/main.nilo
```

## Example

```nilo
from "math_tools" import add, sum_to;
import "messages" as messages;
import "std/json" as json;

let total = add(10, 20);
let payload = {"name": "nilo", "total": total};
print(messages.banner);
print(total);
print(sum_to(5));
print(json.stringify(payload));
```

`examples/math_tools.nilo`:

```nilo
export func add(a: int, b: int) -> int {
    return a + b;
}

export func sum_to(n: int) -> int {
    let i = 0;
    let total = 0;
    while (i <= n) {
        total = total + i;
        i = i + 1;
    }
    return total;
}
```

## Module System

Use `export` to expose values from a file:

```nilo
export let answer = 42;
export func double(x: int) -> int {
    return x * 2;
}
```

Import an entire module:

```nilo
import "tools" as tools;
print(tools.answer);
```

Or import specific names:

```nilo
from "tools" import answer, double;
print(double(answer));
```

Relative imports are resolved from the importing file. The `.nilo` extension is optional.

## Packaging

This repository can be distributed as a Python package during the alpha phase:

```bash
python3 -m build
```

The installed command is:

```bash
nilo path/to/program.nilo
```

Longer term, the interpreter can be ported to Rust once the syntax and runtime behavior settle. The current structure keeps lexer, parser, AST, interpreter, and CLI separated so that migration is straightforward.

## Project Status

Nilo is not production-ready yet. Good next milestones are:

- Static type checking
- Better diagnostics with source snippets
- Standard library modules
- Package registry format
- Rust bytecode VM or native compiler backend
