# Nilo

Niloは、読みやすい構文、シンプルなモジュール、育てやすい実装を目指した小さなプログラミング言語です。

現在の実装はPython製のアルファ版インタプリタです。実行時依存はありません。

## 特徴

- `let` による変数定義
- `func` と `return` による関数
- 数値、文字列、真偽値、リスト、map、添字アクセス
- `if` / `else`、`while`、`for ... in`
- `type` による軽量なレコード風の型宣言
- `export`、`import`、`from ... import ...` によるファイルモジュール
- `std/json`、`std/regex`、`std/fs`、`std/http`、`std/time` などの標準モジュール
- CLI、REPL、プロジェクト初期化、テスト実行、トークン表示、AST表示

## はじめ方

```bash
uv pip install -e .
uv run nilo run examples/main.nilo
```

サブコマンド:

```bash
uv run nilo run examples/main.nilo
uv run nilo test
uv run nilo init my-app
uv run nilo tokens examples/main.nilo
uv run nilo ast examples/main.nilo
```

## コード例

```nilo
from "math_tools" import add, sum_to;
import "messages" as messages;
import "std/json" as json;
import "std/regex" as regex;

let total = add(10, 20);
let payload = {"name": "nilo", "total": total};

print(messages.banner);
print(total);
print(sum_to(5));
print(json.stringify(payload));
print(regex.is_match("^[a-z]+$", "nilo"));
```

## モジュール

値や関数を公開するには `export` を使います。

```nilo
export let answer = 42;

export func double(x: int) -> int {
    return x * 2;
}
```

モジュール全体を読み込む場合:

```nilo
import "tools" as tools;
print(tools.answer);
```

名前を選んで読み込む場合:

```nilo
from "tools" import answer, double;
print(double(answer));
```

相対importは、importしているファイルからの相対パスとして解決されます。`.nilo` 拡張子は省略できます。

## 正規表現

`std/regex` はPythonの正規表現エンジンを利用した強力な正規表現APIです。名前付きキャプチャ、置換、分割、全件検索、フラグ指定に対応しています。

```nilo
import "std/regex" as regex;

let email = regex.find("(?P<user>[\\w.]+)@(?P<host>[\\w.]+)", "dev@example.com");
print(email.named.user);

let words = regex.find_all("\\w+", "Nilo speaks many languages");
print(len(words));

let slug = regex.replace("\\s+", "Nilo Language", "-");
print(slug);
```

利用できる関数:

- `compile(pattern, flags?)`
- `is_match(pattern, text, flags?)`
- `find(pattern, text, flags?)`
- `find_all(pattern, text, flags?)`
- `captures(pattern, text, flags?)`
- `replace(pattern, text, replacement, flags?)`
- `split(pattern, text, flags?)`
- `escape(text)`

フラグは `regex.flags` から利用できます。

```nilo
import "std/regex" as regex;

let flags = regex.flags.ignore_case;
print(regex.is_match("nilo", "NILO", flags));
```

利用可能なフラグ:

- `ignore_case`
- `multiline`
- `dot_all`
- `verbose`
- `ascii`

## パッケージ

アルファ版では、Niloプロジェクトは通常のディレクトリとして共有できます。`Nilo.toml` にパッケージ情報と公開モジュールを書きます。

```toml
[package]
name = "my-package"
version = "0.1.0"
entry = "src/main.nilo"

[exports]
main = "src/main.nilo"
```

将来的には、この形式を使って `nilo add`、`nilo run`、lockfile、パッケージ公開などを実装する予定です。

## 状態

Niloはまだ実験段階です。次の大きな作業候補は、型チェック、より良い診断表示、パッケージ管理、Rust製VMまたはコンパイラバックエンドです。
