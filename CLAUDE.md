# CLAUDE.md

このファイルは、このリポジトリでコードを扱う際にClaude Code（claude.ai/code）にガイダンスを提供します。

## 開発コマンド

### 環境セットアップ
```bash
# 仮想環境を作成
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 開発モードでインストール
pip install -e ".[dev]"
```

### テスト実行
```bash
# すべてのテストを実行
pytest

# 詳細な出力でテストを実行
pytest -v

# 特定のテストファイルを実行
pytest tests/test_server.py
pytest tests/test_edge_cases.py

# 特定のテストを実行
pytest tests/test_server.py::test_list_servers

# カバレッジ付きでテスト実行
pytest --cov=src --cov-report=html
```

### コード品質チェック
```bash
# コードフォーマット
ruff format .

# リント
ruff check .
ruff check . --fix  # 自動修正可能な問題を修正

# 型チェック
mypy src --strict
```

### サーバー実行
```bash
# MCPサーバーを起動
mcp-conf-mcp-server

# カスタム設定ファイルパスを指定して起動
MCP_CONFIG_PATH=/path/to/custom/mcp.json mcp-conf-mcp-server

# Windows環境変数での起動
MCP_CONFIG_PATH=%APPDATA%\Claude\claude_desktop_config.json mcp-conf-mcp-server
```

## アーキテクチャ概要

このプロジェクトは、AWS Q DeveloperとClaude DesktopのMCP設定ファイルを管理するMCPサーバーです。

### コアアーキテクチャ

```
設定ファイル (JSON) ← → MCPサーバー (FastMCP) ← → クライアント (AWS Q/Claude Desktop)
     ↓                        ↓
  バックアップ            ツール定義
                      (list/add/update/remove)
```

### 重要な設計判断

1. **パス展開の多重サポート**:
   - `os.path.expanduser()`: Unix形式のチルダ展開（`~`）
   - `os.path.expandvars()`: Windows環境変数展開（`%APPDATA%`等）
   - 両方を組み合わせることでクロスプラットフォーム対応

2. **アトミックなファイル操作**:
   ```python
   # 一時ファイルに書き込んでから置き換え
   temp_path = CONFIG_PATH.with_suffix(".tmp")
   with open(temp_path, "w") as f:
       json.dump(config.model_dump(exclude_none=True), f, indent=2)
   temp_path.replace(CONFIG_PATH)
   ```

3. **エラーハンドリング階層**:
   - 設定ファイル不在 → 空の設定を返す（非破壊的）
   - JSONパースエラー → 空の設定を返す（既存設定を保護）
   - バックアップ失敗 → ログ記録して処理継続

### ツールの相互作用

- `add_server`: 重複チェック → 失敗時は`update_server`を推奨
- `update_server`: 環境変数のマージ/置換オプション
- `remove_server`: 削除前に自動バックアップ
- `validate_config`: 設定の構造的妥当性を検証

## 重要な実装詳細

### 環境変数の処理（server.py:27-36）
```python
config_path_env = os.environ.get("MCP_CONFIG_PATH", str(DEFAULT_CONFIG_PATH))
CONFIG_PATH = Path(os.path.expandvars(os.path.expanduser(config_path_env)))
```

### Pydanticモデルの使用理由
- 型安全性の確保
- 自動的なJSON検証
- デフォルト値の管理（`Field(default_factory=list)`）

### FastMCPツールのパターン
```python
@mcp.tool(name="tool_name")
async def tool_name(param: Type) -> Dict[str, Any]:
    config = load_config()  # 常に最新の設定を読み込む
    # 処理
    save_config(config)     # 変更時は必ず保存
    return {"key": "value"} # 構造化された応答
```

## テスト戦略

### モックの使用（tests/conftest.py）
```python
@pytest.fixture
def mock_config_path(tmp_path):
    with patch("mcp_conf_mcp_server.server.CONFIG_PATH", tmp_path / "mcp.json"):
        yield
```

### エッジケーステスト重点項目
- 無効なJSON（`{invalid json}`）
- 空のコマンド文字列
- 特殊文字を含むサーバー名
- ファイル権限エラー（chmod 000）

## 注意事項

1. **FastMCPのインポート**:
   - 正: `from mcp.server import FastMCP`
   - 誤: `from mcp import FastMCP`

2. **型アノテーション必須**:
   - 全関数に戻り値の型を明示
   - `mypy --strict`でエラーゼロを維持

3. **Windows対応**:
   - パス区切り文字は`Path`オブジェクトに任せる
   - 環境変数展開は`os.path.expandvars()`を使用

4. **エラーメッセージ**:
   - ユーザー向けエラーには必ず`hint`を含める
   - ログには操作の文脈を含める