# MCP設定エディター

AWS Q DeveloperおよびClaude DesktopのMCP（Model Context Protocol）設定ファイルを管理するためのMCPサーバーです。設定ファイルの読み込み、編集、検証を安全に行うことができます。

## 特徴

- 🔧 **設定管理**: MCPサーバーの追加、更新、削除が簡単に
- 🔍 **検証機能**: 設定ファイルの構造と内容を自動検証
- 💾 **自動バックアップ**: 設定変更時に自動的にバックアップを作成
- 🔐 **安全な操作**: アトミックなファイル書き込みでデータを保護
- 🌍 **環境変数サポート**: カスタム設定ファイルパスの指定が可能
- 📊 **詳細なロギング**: すべての操作を追跡可能

## インストール

### uvxを使用する方法（推奨）

`~/.aws/amazonq/mcp.json`（またはカスタムパス）に以下を追加します：

```json
{
  "mcpServers": {
    "mcp-conf": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/r3-yamauchi/mcp-conf-mcp-server.git",
        "mcp-conf-mcp-server"
      ]
    }
  }
}
```

#### 環境変数について

設定ファイルのパスやバックアップディレクトリをカスタマイズできます：

| 環境変数 | 説明 | デフォルト値 |
|---------|------|------------|
| **MCP_CONFIG_PATH** | MCP設定ファイルのパス | `~/.aws/amazonq/mcp.json` |
| **MCP_BACKUP_DIR** | バックアップディレクトリのパス | 設定ファイルと同じディレクトリの `backups/`<br>例: `~/.aws/amazonq/backups/` |

#### 環境変数を指定する場合

カスタム設定ファイルパスやバックアップディレクトリを指定したい場合：

```json
{
  "mcpServers": {
    "mcp-conf": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/r3-yamauchi/mcp-conf-mcp-server.git",
        "mcp-conf-mcp-server"
      ],
      "env": {
        "MCP_CONFIG_PATH": "/path/to/custom/mcp.json",
        "MCP_BACKUP_DIR": "/path/to/custom/backups"
      }
    }
  }
}
```

#### Claude Desktop向けの設定例

Claude Desktopの設定ファイルを管理する場合（`~/Library/Application Support/Claude/claude_desktop_config.json`に追加）：

```json
{
  "mcpServers": {
    "mcp-conf-claude": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/r3-yamauchi/mcp-conf-mcp-server.git",
        "mcp-conf-mcp-server"
      ],
      "env": {
        "MCP_CONFIG_PATH": "~/Library/Application Support/Claude/claude_desktop_config.json"
      }
    }
  }
}
```

注：`~`（チルダ）は自動的にホームディレクトリに展開されるため、ユーザー名の指定は不要です。

#### Windows向けの設定例

Windowsの場合（`%APPDATA%\Claude\claude_desktop_config.json`に追加）：

```json
{
  "mcpServers": {
    "mcp-conf": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/r3-yamauchi/mcp-conf-mcp-server.git",
        "mcp-conf-mcp-server"
      ],
      "env": {
        "MCP_CONFIG_PATH": "%APPDATA%\\Claude\\claude_desktop_config.json"
      }
    }
  }
}
```

注：Windowsでは環境変数（`%APPDATA%`、`%USERPROFILE%`等）が自動的に展開されます。

### 手動インストール

```bash
# リポジトリをクローン
git clone https://github.com/r3-yamauchi/mcp-conf-mcp-server.git
cd mcp-conf-mcp-server

# 仮想環境を作成（推奨）
python3 -m venv venv

# アクティベート
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# インストール
pip install -e .

# サーバーを実行
mcp-conf-mcp-server
```

### 使用例

```bash
# AWS Q Developer（デフォルト）
mcp-conf-mcp-server

# Claude Desktop向け
MCP_CONFIG_PATH="$HOME/Library/Application Support/Claude/claude_desktop_config.json" mcp-conf-mcp-server

# カスタムバックアップディレクトリも指定
MCP_CONFIG_PATH=/path/to/custom/mcp.json MCP_BACKUP_DIR=/path/to/backups mcp-conf-mcp-server
```

### 対応する設定ファイル

このMCPサーバーは以下の設定ファイルに対応しています：

#### macOS/Linux
- **AWS Q Developer**: `~/.aws/amazonq/mcp.json`
- **Claude Desktop**: `~/Library/Application Support/Claude/claude_desktop_config.json`

#### Windows
- **AWS Q Developer**: `%USERPROFILE%\.aws\amazonq\mcp.json`
- **Claude Desktop**: `%APPDATA%\Claude\claude_desktop_config.json`

#### カスタムパス
- 環境変数 `MCP_CONFIG_PATH` で任意のパスを指定可能
- Unix形式（`~`）とWindows形式（`%USERPROFILE%`、`%APPDATA%`等）の両方に対応

## 利用可能なツール

### 📋 list_servers
設定されている全てのMCPサーバーを一覧表示します。

**例：**
```
/mcp list_servers
```

### 🔍 get_server
特定のMCPサーバーの設定を取得します。

**パラメータ：**
- `name` (string, 必須): サーバーの名前

**例：**
```
/mcp get_server name="my-server"
```

### ➕ add_server
新しいMCPサーバー設定を追加します。

**パラメータ：**
- `name` (string, 必須): サーバーの名前
- `command` (string, 必須): 実行するコマンド
- `args` (array, オプション): コマンドライン引数
- `env` (object, オプション): 環境変数

**例：**
```
/mcp add_server name="my-server" command="uvx" args=["--from", "git+https://github.com/user/repo.git", "package-name"]
```

### 🔄 update_server
既存のMCPサーバー設定を更新します。

**パラメータ：**
- `name` (string, 必須): サーバーの名前
- `command` (string, オプション): 新しいコマンド
- `args` (array, オプション): 新しい引数
- `env` (object, オプション): 追加/更新する環境変数
- `replace_env` (boolean, オプション): 環境変数を完全に置き換える場合はtrue

**例：**
```
# コマンドを更新
/mcp update_server name="my-server" command="python"

# 環境変数を追加（既存の環境変数とマージ）
/mcp update_server name="my-server" env={"API_KEY": "secret", "DEBUG": "true"}

# 環境変数を完全に置き換え
/mcp update_server name="my-server" env={"NEW_VAR": "value"} replace_env=true
```

### ❌ remove_server
MCPサーバー設定を削除します。

**パラメータ：**
- `name` (string, 必須): サーバーの名前

**例：**
```
/mcp remove_server name="my-server"
```

### ✅ validate_config
現在のMCP設定ファイルを検証します。

**例：**
```
/mcp validate_config
```

### 📤 export_config
MCP設定全体をJSON形式でエクスポートします。

**例：**
```
/mcp export_config
```

## 使用例

### 基本的なワークフロー

```bash
# 1. 現在の設定を確認
/mcp list_servers

# 2. 新しいサーバーを追加
/mcp add_server name="code-analyzer" command="uvx" args=["--from", "git+https://github.com/example/analyzer.git", "analyzer"]

# 3. 環境変数を設定
/mcp update_server name="code-analyzer" env={"ANALYSIS_LEVEL": "detailed"}

# 4. 設定を検証
/mcp validate_config

# 5. 設定をエクスポート（バックアップ用）
/mcp export_config
```

### Windows環境での使用例

Windows環境で環境変数を使用する場合：

```bash
# コマンドプロンプト
set MCP_CONFIG_PATH=%APPDATA%\Claude\claude_desktop_config.json
mcp-conf-mcp-server

# PowerShell
$env:MCP_CONFIG_PATH = "$env:APPDATA\Claude\claude_desktop_config.json"
mcp-conf-mcp-server
```

## 開発

### セットアップ

```bash
# 開発依存関係をインストール
pip install -e ".[dev]"
```

### コマンド

```bash
# テストを実行
pytest
pytest -v  # 詳細表示

# コード品質チェック
ruff format .  # フォーマット
ruff check .   # リント
mypy src       # 型チェック
```

### プロジェクト構造

```
mcp-conf-mcp-server/
├── src/
│   └── mcp_conf_mcp_server/
│       ├── __init__.py      # パッケージ初期化
│       ├── __main__.py      # エントリーポイント
│       └── server.py        # MCPサーバー実装
├── tests/
│   ├── test_server.py       # 基本機能テスト
│   └── test_edge_cases.py   # エッジケーステスト
├── pyproject.toml           # プロジェクト設定
├── README.md               # このファイル
├── CLAUDE.md               # 開発者向けドキュメント
└── LICENSE                 # MITライセンス
```

## アーキテクチャ

### 主要コンポーネント

- **MCPサーバー実装**: FastMCPフレームワークを使用
- **設定管理**: Pydanticモデルによる型安全な設定
- **バックアップシステム**: タイムスタンプ付き自動バックアップ
- **エラーハンドリング**: 包括的な例外処理とロギング

### セキュリティ機能

- アトミックなファイル書き込み（データ破損を防止）
- 設定変更前の自動バックアップ
- JSONスキーマ検証
- 詳細なエラーメッセージとログ

## トラブルシューティング

### よくある問題

1. **設定ファイルが見つからない**
   - ファイルパスを確認: `echo $MCP_CONFIG_PATH`
   - デフォルトパス: `~/.aws/amazonq/mcp.json`

2. **権限エラー**
   - ファイルの権限を確認: `ls -la ~/.aws/amazonq/mcp.json`
   - 必要に応じて権限を修正: `chmod 644 ~/.aws/amazonq/mcp.json`

3. **JSONパースエラー**
   - `validate_config`ツールで検証
   - バックアップから復元可能

## 貢献

プルリクエストを歓迎します！以下のガイドラインに従ってください：

1. フォークしてフィーチャーブランチを作成
2. テストを追加（既存のテストがパスすることを確認）
3. コードフォーマットを実行（`ruff format`）
4. プルリクエストを送信

## ライセンス

MIT License - 詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 作者

- GitHub: [@r3-yamauchi](https://github.com/r3-yamauchi)