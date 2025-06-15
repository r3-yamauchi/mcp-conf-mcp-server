"""MCP設定サーバーのエントリーポイント。

このモジュールは、コマンドラインからMCPサーバーを起動する際の
エントリーポイントを提供します。
"""

import sys
import logging
from pathlib import Path

from dotenv import load_dotenv

from .server import run_server

# ロギングの基本設定
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# ロガーの初期化
logger = logging.getLogger(__name__)


def main() -> None:
    """MCP設定サーバーのメインエントリーポイント。

    環境変数の読み込み、サーバーの起動、エラーハンドリングを行います。
    """
    # .envファイルが存在する場合は環境変数を読み込む
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    try:
        # サーバーの起動ログを出力
        logger.info("Starting MCP Configuration Server...")
        run_server()
    except KeyboardInterrupt:
        # Ctrl+Cによる終了
        logger.info("Server stopped by user")
    except Exception as e:
        # その他のエラー
        logger.error(f"Server failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 直接実行された場合のみメイン関数を実行
    main()
