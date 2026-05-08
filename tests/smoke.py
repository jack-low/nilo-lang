from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nilo.runtime import run_file, run_source



def test_inline_program():
    run_source(
        """
        func add(a: int, b: int) -> int {
            return a + b;
        }
        let value = add(2, 3);
        print(value);
        """
    )


def test_example_program():
    run_file(ROOT / "examples" / "main.nilo")


if __name__ == "__main__":
    test_inline_program()
    test_example_program()
