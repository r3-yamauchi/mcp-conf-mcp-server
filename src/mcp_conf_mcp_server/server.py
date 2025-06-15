"""AWS Q Developer MCP設定ファイルを編集するためのMCPサーバー実装。

このモジュールは、AWS Q DeveloperのMCP設定ファイル（~/.aws/amazonq/mcp.json）を
管理するためのツールを提供します。設定の追加、更新、削除、検証などの操作が可能です。
"""

import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from mcp.server import FastMCP
from pydantic import BaseModel, Field, ValidationError

# ロガーの初期化
logger = logging.getLogger(__name__)

# MCPサーバーのインスタンスを初期化
mcp = FastMCP("MCP Configuration Editor for AWS Q Developer")

# AWS Q DeveloperのMCP設定ファイルパス
# 環境変数で指定可能、デフォルトは ~/.aws/amazonq/mcp.json
DEFAULT_CONFIG_PATH = Path.home() / ".aws" / "amazonq" / "mcp.json"
config_path_env = os.environ.get("MCP_CONFIG_PATH", str(DEFAULT_CONFIG_PATH))
# ~を含むパスを展開（Unix/Linux/macOS）およびWindows環境変数を展開
CONFIG_PATH = Path(os.path.expandvars(os.path.expanduser(config_path_env)))

# バックアップディレクトリ
# 環境変数で指定可能、デフォルトは設定ファイルと同じディレクトリの backups/
DEFAULT_BACKUP_DIR = CONFIG_PATH.parent / "backups"
backup_dir_env = os.environ.get("MCP_BACKUP_DIR", str(DEFAULT_BACKUP_DIR))
# ~を含むパスを展開（Unix/Linux/macOS）およびWindows環境変数を展開
BACKUP_DIR = Path(os.path.expandvars(os.path.expanduser(backup_dir_env)))


class ServerConfig(BaseModel):
    """MCPサーバーの設定を表すモデル。

    Attributes:
        command: 実行するコマンド（例: "python", "uvx", "node"）
        args: コマンドライン引数のリスト
        env: 環境変数の辞書（オプション）
    """

    command: str
    args: list[str] = Field(default_factory=list)
    env: Optional[Dict[str, str]] = None


class MCPConfig(BaseModel):
    """mcp.json設定ファイルの構造を表すモデル。

    Attributes:
        mcpServers: サーバー名をキーとし、ServerConfigを値とする辞書
    """

    mcpServers: Dict[str, ServerConfig] = Field(default_factory=dict)


def load_config() -> MCPConfig:
    """現在のMCP設定を読み込む。

    設定ファイルが存在しない場合や読み込みエラーが発生した場合は、
    空の設定を返します。

    Returns:
        MCPConfig: 読み込まれた設定、またはデフォルトの空設定
    """
    if not CONFIG_PATH.exists():
        # 設定ファイルが存在しない場合は空の設定を返す
        logger.info(f"Configuration file not found at {CONFIG_PATH}")
        return MCPConfig()

    try:
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
        config = MCPConfig(**data)
        logger.debug(f"Loaded configuration with {len(config.mcpServers)} servers")
        return config
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON configuration: {e}")
        # エラーが発生した場合も空の設定を返す（既存の設定を破壊しない）
        return MCPConfig()
    except ValidationError as e:
        logger.error(f"Configuration validation failed: {e}")
        return MCPConfig()
    except Exception as e:
        logger.error(f"Unexpected error loading configuration: {e}")
        return MCPConfig()


def create_backup() -> Optional[Path]:
    """現在の設定ファイルのバックアップを作成する。

    Returns:
        Optional[Path]: バックアップファイルのパス、またはNone
    """
    if not CONFIG_PATH.exists():
        return None

    try:
        # バックアップディレクトリを作成
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        # タイムスタンプ付きのバックアップファイル名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"mcp_{timestamp}.json"

        # ファイルをコピー
        shutil.copy2(CONFIG_PATH, backup_path)
        logger.info(f"Created backup at {backup_path}")
        return backup_path
    except Exception as e:
        logger.warning(f"Failed to create backup: {e}")
        return None


def save_config(config: MCPConfig, create_backup_file: bool = True) -> None:
    """MCP設定をディスクに保存する。

    必要に応じて親ディレクトリを作成し、設定をJSON形式で保存します。
    Noneの値は除外され、読みやすいように2スペースでインデントされます。

    Args:
        config: 保存するMCP設定
        create_backup_file: 保存前にバックアップを作成するかどうか

    Raises:
        Exception: 保存に失敗した場合
    """
    try:
        # バックアップを作成
        if create_backup_file and CONFIG_PATH.exists():
            try:
                create_backup()
            except Exception as e:
                logger.warning(f"Failed to create backup, continuing with save: {e}")

        # 親ディレクトリが存在しない場合は作成
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

        # 一時ファイルに書き込んでからアトミックに置き換え
        temp_path = CONFIG_PATH.with_suffix(".tmp")
        with open(temp_path, "w") as f:
            json.dump(config.model_dump(exclude_none=True), f, indent=2)
            f.write("\n")  # 最後に改行を追加

        # アトミックに置き換え
        temp_path.replace(CONFIG_PATH)
        logger.info(f"Configuration saved successfully to {CONFIG_PATH}")
    except Exception as e:
        logger.error(f"Failed to save configuration: {e}")
        raise


@mcp.tool(name="list_servers")
async def list_servers() -> Dict[str, Any]:
    """設定されている全てのMCPサーバーをリスト表示する。

    Returns:
        Dict[str, Any]: サーバーのリストと設定ファイルのパスを含む辞書
            - servers: 各サーバーの設定情報のリスト
            - config_path: 設定ファイルのパス
    """
    config = load_config()

    # 各サーバーの情報をリスト化
    servers = []
    for name, server_config in config.mcpServers.items():
        servers.append(
            {"name": name, "command": server_config.command, "args": server_config.args, "env": server_config.env}
        )

    return {"servers": servers, "config_path": str(CONFIG_PATH)}


@mcp.tool(name="get_server")
async def get_server(name: str) -> Dict[str, Any]:
    """特定のMCPサーバーの設定を取得する。

    Args:
        name: 取得するサーバーの名前

    Returns:
        Dict[str, Any]: サーバーの設定情報、またはエラー情報
    """
    config = load_config()

    if name not in config.mcpServers:
        # サーバーが見つからない場合はエラーと利用可能なサーバーリストを返す
        logger.warning(f"Attempted to get non-existent server: {name}")
        return {"error": f"Server '{name}' not found", "available_servers": list(config.mcpServers.keys())}

    # サーバー情報を返す
    server = config.mcpServers[name]
    logger.debug(f"Retrieved server configuration for: {name}")
    return {"name": name, "command": server.command, "args": server.args, "env": server.env}


@mcp.tool(name="add_server")
async def add_server(
    name: str, command: str, args: Optional[list[str]] = None, env: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """新しいMCPサーバー設定を追加する。

    既に同名のサーバーが存在する場合はエラーを返します。

    Args:
        name: 新しいサーバーの名前
        command: 実行するコマンド
        args: コマンドライン引数（オプション）
        env: 環境変数（オプション）

    Returns:
        Dict[str, Any]: 成功メッセージと追加されたサーバー情報、またはエラー情報
    """
    config = load_config()

    if name in config.mcpServers:
        # 同名のサーバーが既に存在する場合はエラーを返す
        logger.warning(f"Attempted to add duplicate server: {name}")
        return {
            "error": f"Server '{name}' already exists",
            "hint": "Use update_server to modify existing configuration",
        }

    # 新しいサーバー設定を作成
    server_config = ServerConfig(command=command, args=args or [], env=env)

    # 設定に追加して保存
    config.mcpServers[name] = server_config

    try:
        save_config(config)
        logger.info(f"Successfully added server: {name}")
        return {
            "message": f"Server '{name}' added successfully",
            "server": {
                "name": name,
                "command": server_config.command,
                "args": server_config.args,
                "env": server_config.env,
            },
        }
    except Exception as e:
        logger.error(f"Failed to save configuration after adding server {name}: {e}")
        return {"error": f"Failed to save configuration: {str(e)}", "hint": "Check file permissions and disk space"}


@mcp.tool(name="update_server")
async def update_server(
    name: str,
    command: Optional[str] = None,
    args: Optional[list[str]] = None,
    env: Optional[Dict[str, str]] = None,
    replace_env: bool = False,
) -> Dict[str, Any]:
    """既存のMCPサーバー設定を更新する。

    指定されたフィールドのみが更新されます。

    Args:
        name: 更新するサーバーの名前
        command: 新しいコマンド（オプション）
        args: 新しい引数リスト（オプション）
        env: 追加/更新する環境変数（オプション）
        replace_env: Trueの場合、環境変数を完全に置き換える（デフォルト: False）

    Returns:
        Dict[str, Any]: 成功メッセージと更新されたサーバー情報、またはエラー情報
    """
    config = load_config()

    if name not in config.mcpServers:
        # サーバーが見つからない場合はエラーを返す
        logger.warning(f"Attempted to update non-existent server: {name}")
        return {"error": f"Server '{name}' not found", "available_servers": list(config.mcpServers.keys())}

    server = config.mcpServers[name]

    # 指定されたフィールドを更新
    if command is not None:
        server.command = command

    if args is not None:
        server.args = args

    if env is not None:
        if replace_env or server.env is None:
            # 環境変数を完全に置き換える、または初回設定
            server.env = env
        else:
            # 既存の環境変数にマージ
            server.env.update(env)

    # 変更を保存
    try:
        save_config(config)
        logger.info(f"Successfully updated server: {name}")
        return {
            "message": f"Server '{name}' updated successfully",
            "server": {"name": name, "command": server.command, "args": server.args, "env": server.env},
        }
    except Exception as e:
        logger.error(f"Failed to save configuration after updating server {name}: {e}")
        return {"error": f"Failed to save configuration: {str(e)}", "hint": "Check file permissions and disk space"}


@mcp.tool(name="remove_server")
async def remove_server(name: str) -> Dict[str, Any]:
    """MCPサーバー設定を削除する。

    Args:
        name: 削除するサーバーの名前

    Returns:
        Dict[str, Any]: 成功メッセージと残りのサーバーリスト、またはエラー情報
    """
    config = load_config()

    if name not in config.mcpServers:
        # サーバーが見つからない場合はエラーを返す
        logger.warning(f"Attempted to remove non-existent server: {name}")
        return {"error": f"Server '{name}' not found", "available_servers": list(config.mcpServers.keys())}

    # サーバーを削除して保存
    del config.mcpServers[name]

    try:
        save_config(config)
        logger.info(f"Successfully removed server: {name}")
        return {"message": f"Server '{name}' removed successfully", "remaining_servers": list(config.mcpServers.keys())}
    except Exception as e:
        logger.error(f"Failed to save configuration after removing server {name}: {e}")
        return {"error": f"Failed to save configuration: {str(e)}", "hint": "Check file permissions and disk space"}


@mcp.tool(name="validate_config")
async def validate_config() -> Dict[str, Any]:
    """現在のMCP設定ファイルを検証する。

    設定ファイルの存在、JSON形式の妥当性、各サーバー設定の
    必須フィールドをチェックします。

    Returns:
        Dict[str, Any]: 検証結果を含む辞書
            - valid: 検証が成功したかどうか
            - servers_count: サーバー数
            - servers: サーバー名のリスト
            - issues: 見つかった問題のリスト（ある場合）
            - error: エラーメッセージ（ある場合）
    """
    if not CONFIG_PATH.exists():
        # 設定ファイルが存在しない場合
        return {
            "valid": False,
            "error": f"Configuration file not found at {CONFIG_PATH}",
            "hint": "Use add_server to create initial configuration",
        }

    try:
        # JSONファイルを読み込んでパース
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)

        # Pydanticモデルで検証
        config = MCPConfig(**data)

        # 各サーバー設定の検証
        issues = []
        for name, server in config.mcpServers.items():
            if not server.command:
                issues.append(f"Server '{name}' has empty command")

        return {
            "valid": len(issues) == 0,
            "servers_count": len(config.mcpServers),
            "servers": list(config.mcpServers.keys()),
            "issues": issues if issues else None,
        }

    except json.JSONDecodeError as e:
        # JSONパースエラー
        return {"valid": False, "error": f"Invalid JSON: {str(e)}"}
    except Exception as e:
        # その他の検証エラー
        return {"valid": False, "error": f"Validation error: {str(e)}"}


@mcp.tool(name="export_config")
async def export_config() -> Dict[str, Any]:
    """MCP設定全体をJSON形式でエクスポートする。

    現在の設定を表示や別の場所へのコピー用に取得します。

    Returns:
        Dict[str, Any]: 設定全体と設定ファイルパスを含む辞書
            - config: 現在の設定の完全な内容
            - config_path: 設定ファイルのパス
    """
    config = load_config()

    return {"config": config.model_dump(exclude_none=True), "config_path": str(CONFIG_PATH)}


def run_server() -> None:
    """MCPサーバーを起動する。

    FastMCPフレームワークを使用してサーバーを実行し、
    定義されたツールを利用可能にします。
    """
    mcp.run()
