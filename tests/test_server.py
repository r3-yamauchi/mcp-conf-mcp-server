"""MCP設定サーバーのテスト。

このモジュールには、MCPサーバーの各機能をテストするための
単体テストが含まれています。一時ファイルを使用してテスト環境を
分離し、実際の設定ファイルに影響を与えないようにしています。
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_conf_mcp_server.server import (
    add_server,
    get_server,
    list_servers,
    remove_server,
    update_server,
    validate_config,
)


@pytest.fixture
def temp_config_file():
    """テスト用の一時設定ファイルを作成するフィクスチャ。

    テスト実行前に一時ファイルを作成し、テスト終了後に
    自動的に削除します。

    Yields:
        Path: 一時設定ファイルのパス
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        # テスト用の初期設定を作成
        config = {"mcpServers": {"test-server": {"command": "python", "args": ["-m", "test_module"]}}}
        json.dump(config, f)
        temp_path = Path(f.name)

    yield temp_path

    # テスト終了後にクリーンアップ
    temp_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_list_servers(temp_config_file):
    """全てのサーバーをリスト表示する機能のテスト。

    設定ファイルからサーバー情報を正しく読み込んで
    リスト化できることを検証します。
    """
    with patch("mcp_conf_mcp_server.server.CONFIG_PATH", temp_config_file):
        result = await list_servers()

        # 結果の検証
        assert "servers" in result
        assert len(result["servers"]) == 1
        assert result["servers"][0]["name"] == "test-server"
        assert result["servers"][0]["command"] == "python"


@pytest.mark.asyncio
async def test_get_server(temp_config_file):
    """特定のサーバー情報を取得する機能のテスト。

    存在するサーバーと存在しないサーバーの両方のケースを
    テストします。
    """
    with patch("mcp_conf_mcp_server.server.CONFIG_PATH", temp_config_file):
        # 存在するサーバーの取得
        result = await get_server("test-server")

        assert result["name"] == "test-server"
        assert result["command"] == "python"
        assert result["args"] == ["-m", "test_module"]

        # 存在しないサーバーの取得（エラーケース）
        result = await get_server("nonexistent")
        assert "error" in result


@pytest.mark.asyncio
async def test_add_server(temp_config_file):
    """新しいサーバーを追加する機能のテスト。

    正常な追加と重複エラーの両方をテストします。
    """
    with patch("mcp_conf_mcp_server.server.CONFIG_PATH", temp_config_file):
        # 新しいサーバーを追加
        result = await add_server(
            name="new-server", command="uvx", args=["--from", "git+https://example.com/repo.git", "package"]
        )

        assert "message" in result
        assert "new-server" in result["message"]

        # 追加されたことを確認
        servers = await list_servers()
        assert len(servers["servers"]) == 2

        # 重複サーバーの追加を試みる（エラーケース）
        result = await add_server(name="new-server", command="python")
        assert "error" in result


@pytest.mark.asyncio
async def test_update_server(temp_config_file):
    """既存のサーバーを更新する機能のテスト。

    コマンドや引数の更新、存在しないサーバーの
    更新試行をテストします。
    """
    with patch("mcp_conf_mcp_server.server.CONFIG_PATH", temp_config_file):
        # サーバー設定を更新
        result = await update_server(name="test-server", command="node", args=["index.js"])

        assert "message" in result

        # 更新が反映されたことを確認
        server = await get_server("test-server")
        assert server["command"] == "node"
        assert server["args"] == ["index.js"]

        # 存在しないサーバーの更新を試みる（エラーケース）
        result = await update_server(name="nonexistent", command="python")
        assert "error" in result


@pytest.mark.asyncio
async def test_remove_server(temp_config_file):
    """サーバーを削除する機能のテスト。

    正常な削除と存在しないサーバーの削除試行を
    テストします。
    """
    with patch("mcp_conf_mcp_server.server.CONFIG_PATH", temp_config_file):
        # サーバーを削除
        result = await remove_server("test-server")

        assert "message" in result
        assert "test-server" in result["message"]

        # 削除されたことを確認
        servers = await list_servers()
        assert len(servers["servers"]) == 0

        # 存在しないサーバーの削除を試みる（エラーケース）
        result = await remove_server("nonexistent")
        assert "error" in result


@pytest.mark.asyncio
async def test_validate_config(temp_config_file):
    """設定ファイルの検証機能のテスト。

    正常な設定ファイルが正しく検証されることを
    確認します。
    """
    with patch("mcp_conf_mcp_server.server.CONFIG_PATH", temp_config_file):
        result = await validate_config()

        # 検証結果の確認
        assert result["valid"] is True
        assert result["servers_count"] == 1
        assert "test-server" in result["servers"]
