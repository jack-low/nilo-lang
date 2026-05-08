# Nilo Package Draft

Nilo packages are plain directories that can be hosted on GitHub, copied locally, or published later to a registry.

## Manifest

Use `Nilo.toml` at the package root:

```toml
[package]
name = "my-package"
version = "0.1.0"
description = "Reusable Nilo utilities."
entry = "src/main.nilo"

[exports]
math = "src/math.nilo"
strings = "src/strings.nilo"
```

The current interpreter does not require this file to run modules. It is a stable project convention for sharing code before a package manager exists.

## Recommended Layout

```text
my-package/
  Nilo.toml
  README.md
  src/
    main.nilo
    math.nilo
  tests/
    smoke.nilo
```

## Module Imports

Relative imports use source files directly:

```nilo
from "math" import add;
import "strings" as strings;
```

The `.nilo` extension is optional. Imports are resolved relative to the file doing the import.

## Distribution Today

For now, distribute packages by GitHub URL or by copying the package directory into a project.

Recommended release checklist:

1. Add a `Nilo.toml` manifest.
2. Keep public modules listed under `[exports]`.
3. Tag releases with semantic versions such as `v0.1.0`.
4. Include examples that can run with `python3 -m nilo path/to/example.nilo`.

## Future Package Manager

A future `nilo` package manager can use this same manifest to support:

- `nilo init`
- `nilo add github:user/repo`
- `nilo run`
- lockfiles
- package publishing
