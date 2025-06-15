"""エッジケースと例外処理のテスト。

このモジュールには、エラーケース、境界条件、例外処理などの
テストが含まれています。
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from mcp_conf_mcp_server.server import (
    add_server,
    create_backup,
    export_config,
    load_config,
    save_config,
    update_server,
    validate_config,
    MCPConfig,
    ServerConfig,
)


@pytest.mark.asyncio
async def test_add_server_with_empty_name():
    """空のサーバー名で追加しようとした場合のテスト。"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        config = {"mcpServers": {}}
        json.dump(config, f)
        temp_path = Path(f.name)

    try:
        with patch("mcp_conf_mcp_server.server.CONFIG_PATH", temp_path):
            # 空文字列の名前でサーバーを追加
            result = await add_server(name="", command="python")
            
            # 空文字列でも追加できるが、推奨されない
            assert "message" in result or "error" in result
    finally:
        temp_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_update_server_env_merge():
    """環境変数のマージ機能のテスト。"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        config = {
            "mcpServers": {
                "test-server": {
                    "command": "python",
                    "args": [],
                    "env": {"VAR1": "value1", "VAR2": "value2"}
                }
            }
        }
        json.dump(config, f)
        temp_path = Path(f.name)

    try:
        with patch("mcp_conf_mcp_server.server.CONFIG_PATH", temp_path):
            # 環境変数を部分的に更新（マージ）
            result = await update_server(
                name="test-server",
                env={"VAR2": "new_value", "VAR3": "value3"}
            )
            
            assert "message" in result
            
            # 設定を読み込んで確認
            with open(temp_path, "r") as f:
                data = json.load(f)
            
            env = data["mcpServers"]["test-server"]["env"]
            assert env["VAR1"] == "value1"  # 既存の値は保持
            assert env["VAR2"] == "new_value"  # 更新された
            assert env["VAR3"] == "value3"  # 新しく追加された
    finally:
        temp_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_update_server_env_replace():
    """環境変数の完全置換機能のテスト。"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        config = {
            "mcpServers": {
                "test-server": {
                    "command": "python",
                    "args": [],
                    "env": {"VAR1": "value1", "VAR2": "value2"}
                }
            }
        }
        json.dump(config, f)
        temp_path = Path(f.name)

    try:
        with patch("mcp_conf_mcp_server.server.CONFIG_PATH", temp_path):
            # 環境変数を完全に置き換え
            result = await update_server(
                name="test-server",
                env={"NEW_VAR": "new_value"},
                replace_env=True
            )
            
            assert "message" in result
            
            # 設定を読み込んで確認
            with open(temp_path, "r") as f:
                data = json.load(f)
            
            env = data["mcpServers"]["test-server"]["env"]
            assert "VAR1" not in env  # 古い変数は削除された
            assert "VAR2" not in env  # 古い変数は削除された
            assert env["NEW_VAR"] == "new_value"  # 新しい変数のみ存在
    finally:
        temp_path.unlink(missing_ok=True)


def test_load_config_with_invalid_json():
    """無効なJSONファイルの読み込みテスト。"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("{ invalid json }")
        temp_path = Path(f.name)

    try:
        with patch("mcp_conf_mcp_server.server.CONFIG_PATH", temp_path):
            config = load_config()
            
            # エラーが発生しても空の設定を返す
            assert isinstance(config, MCPConfig)
            assert len(config.mcpServers) == 0
    finally:
        temp_path.unlink(missing_ok=True)


def test_load_config_with_invalid_structure():
    """無効な構造のJSONファイルの読み込みテスト。"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        # mcpServersが文字列（正しくは辞書であるべき）
        config = {"mcpServers": "invalid"}
        json.dump(config, f)
        temp_path = Path(f.name)

    try:
        with patch("mcp_conf_mcp_server.server.CONFIG_PATH", temp_path):
            config = load_config()
            
            # バリデーションエラーが発生しても空の設定を返す
            assert isinstance(config, MCPConfig)
            assert len(config.mcpServers) == 0
    finally:
        temp_path.unlink(missing_ok=True)


def test_create_backup():
    """バックアップ作成機能のテスト。"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        config = {"mcpServers": {"test": {"command": "python"}}}
        json.dump(config, f)
        temp_path = Path(f.name)

    with tempfile.TemporaryDirectory() as backup_dir:
        backup_dir_path = Path(backup_dir)
        
        with patch("mcp_conf_mcp_server.server.CONFIG_PATH", temp_path):
            with patch("mcp_conf_mcp_server.server.BACKUP_DIR", backup_dir_path):
                # バックアップを作成
                backup_path = create_backup()
                
                assert backup_path is not None
                assert backup_path.exists()
                assert backup_path.suffix == ".json"
                assert "mcp_" in backup_path.name
                
                # バックアップの内容を確認
                with open(backup_path, "r") as f:
                    backup_data = json.load(f)
                
                assert backup_data == config
    
    temp_path.unlink(missing_ok=True)


def test_create_backup_no_config_file():
    """設定ファイルが存在しない場合のバックアップ作成テスト。"""
    non_existent_path = Path("/tmp/non_existent_config.json")
    
    with patch("mcp_conf_mcp_server.server.CONFIG_PATH", non_existent_path):
        backup_path = create_backup()
        
        # 設定ファイルが存在しない場合はNoneを返す
        assert backup_path is None


def test_save_config_with_backup_error():
    """バックアップ作成に失敗しても保存は続行されることのテスト。"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        config = {"mcpServers": {}}
        json.dump(config, f)
        temp_path = Path(f.name)

    try:
        with patch("mcp_conf_mcp_server.server.CONFIG_PATH", temp_path):
            # create_backupが例外を発生させるようにモック
            with patch("mcp_conf_mcp_server.server.create_backup", side_effect=Exception("Backup failed")):
                # 新しい設定を保存
                new_config = MCPConfig(mcpServers={"new-server": ServerConfig(command="node")})
                
                # バックアップが失敗しても保存は成功するはず
                save_config(new_config)
                
                # 保存された内容を確認
                with open(temp_path, "r") as f:
                    data = json.load(f)
                
                assert "new-server" in data["mcpServers"]
    finally:
        temp_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_validate_config_with_missing_file():
    """設定ファイルが存在しない場合の検証テスト。"""
    non_existent_path = Path("/tmp/non_existent_config.json")
    
    with patch("mcp_conf_mcp_server.server.CONFIG_PATH", non_existent_path):
        result = await validate_config()
        
        assert result["valid"] is False
        assert "error" in result
        assert "not found" in result["error"]
        assert "hint" in result


@pytest.mark.asyncio
async def test_validate_config_with_empty_command():
    """空のコマンドを持つサーバーの検証テスト。"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        config = {
            "mcpServers": {
                "test-server": {
                    "command": "",  # 空のコマンド
                    "args": []
                }
            }
        }
        json.dump(config, f)
        temp_path = Path(f.name)

    try:
        with patch("mcp_conf_mcp_server.server.CONFIG_PATH", temp_path):
            result = await validate_config()
            
            assert result["valid"] is False
            assert "issues" in result
            assert len(result["issues"]) > 0
            assert "empty command" in result["issues"][0]
    finally:
        temp_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_export_config():
    """設定のエクスポート機能のテスト。"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        config = {
            "mcpServers": {
                "server1": {"command": "python", "args": ["-m", "module1"]},
                "server2": {"command": "node", "args": ["index.js"], "env": {"NODE_ENV": "production"}}
            }
        }
        json.dump(config, f)
        temp_path = Path(f.name)

    try:
        with patch("mcp_conf_mcp_server.server.CONFIG_PATH", temp_path):
            result = await export_config()
            
            assert "config" in result
            assert "config_path" in result
            
            exported_config = result["config"]
            assert "mcpServers" in exported_config
            assert len(exported_config["mcpServers"]) == 2
            assert "server1" in exported_config["mcpServers"]
            assert "server2" in exported_config["mcpServers"]
            
            # 環境変数が正しくエクスポートされることを確認
            assert exported_config["mcpServers"]["server2"]["env"]["NODE_ENV"] == "production"
    finally:
        temp_path.unlink(missing_ok=True)


def test_save_config_file_permission_error():
    """ファイル権限エラーのテスト。"""
    config = MCPConfig(mcpServers={"test": ServerConfig(command="python")})
    
    # 書き込み権限のないディレクトリを指定
    readonly_path = Path("/root/test.json")  # 通常は書き込み権限がない
    
    with patch("mcp_conf_mcp_server.server.CONFIG_PATH", readonly_path):
        # 権限エラーで例外が発生することを確認
        with pytest.raises(Exception):
            save_config(config)


@pytest.mark.asyncio
async def test_server_with_special_characters():
    """特殊文字を含むサーバー名のテスト。"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        config = {"mcpServers": {}}
        json.dump(config, f)
        temp_path = Path(f.name)

    try:
        with patch("mcp_conf_mcp_server.server.CONFIG_PATH", temp_path):
            # 特殊文字を含む名前でサーバーを追加
            special_names = [
                "server-with-dash",
                "server.with.dots",
                "server_with_underscore",
                "server@with@at",
                "サーバー日本語",
                "server with spaces"
            ]
            
            for name in special_names:
                result = await add_server(name=name, command="python")
                assert "message" in result, f"Failed to add server with name: {name}"
                
            # 追加されたサーバーを確認
            with open(temp_path, "r") as f:
                data = json.load(f)
            
            assert len(data["mcpServers"]) == len(special_names)
            for name in special_names:
                assert name in data["mcpServers"]
    finally:
        temp_path.unlink(missing_ok=True)