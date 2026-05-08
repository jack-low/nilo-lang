from pathlib import Path
import re


LOCATION_RE = re.compile(r"^(?P<file>.+):(?P<line>\d+):(?P<column>\d+): (?P<message>.+)$")


def format_error(exc: Exception) -> str:
    text = str(exc)
    match = LOCATION_RE.match(text)
    if not match:
        return f"nilo: {text}"

    filename = match.group("file")
    line = int(match.group("line"))
    column = int(match.group("column"))
    message = match.group("message")
    out = [f"nilo: {filename}:{line}:{column}: {message}"]

    path = Path(filename)
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()
        if 1 <= line <= len(lines):
            source_line = lines[line - 1]
            out.append(source_line)
            out.append(" " * max(column - 1, 0) + "^")
    return "\n".join(out)
