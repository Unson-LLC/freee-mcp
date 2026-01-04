#!/usr/bin/env python3
"""freee MCP Server - メインエントリーポイント"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server

# 絶対importに変更（スタンドアロン実行対応）
sys.path.insert(0, str(Path(__file__).parent))
from auth import FreeeOAuth, authenticate
from freee_client import FreeeAPIClient
from token_store import TokenStore
from tools import register_tools

load_dotenv()


class FreeeMCPServer:
    """freee MCP Server"""

    def __init__(self):
        self.server = Server("freee-mcp")
        self.client: Optional[FreeeAPIClient] = None
        self.token_store: Optional[TokenStore] = None
        self.oauth: Optional[FreeeOAuth] = None

        # 環境変数を読み込み
        self.client_id = os.getenv("FREEE_CLIENT_ID")
        self.client_secret = os.getenv("FREEE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("FREEE_REDIRECT_URI", "http://localhost:8080/callback")
        self.encryption_key = os.getenv("TOKEN_ENCRYPTION_KEY")
        self.base_url = os.getenv("FREEE_BASE_URL", "https://api.freee.co.jp")
        self.company_id = int(os.getenv("FREEE_COMPANY_ID", "0"))

        if not all([self.client_id, self.client_secret, self.encryption_key]):
            raise RuntimeError(
                "環境変数が不足しています: FREEE_CLIENT_ID, FREEE_CLIENT_SECRET, TOKEN_ENCRYPTION_KEY"
            )

        # TokenStoreとOAuthを初期化
        self.token_store = TokenStore(self.encryption_key)
        self.oauth = FreeeOAuth(
            self.client_id,
            self.client_secret,
            self.redirect_uri,
        )

    def _refresh_token_callback(self) -> dict:
        """tokenリフレッシュ時のコールバック"""
        token_data = self.token_store.load_token()
        if not token_data or not token_data.get("refresh_token"):
            raise RuntimeError("リフレッシュトークンがありません。再認証してください。")

        new_token = self.oauth.refresh_access_token(token_data["refresh_token"])
        self.token_store.save_token(new_token)
        return new_token

    def get_client(self) -> FreeeAPIClient:
        """FreeeAPIClientを取得（遅延初期化）"""
        if self.client:
            return self.client

        # tokenをロード
        token_data = self.token_store.load_token()
        if not token_data:
            # 初回認証が必要
            print("⚠️ tokenが見つかりません。初回認証を実行してください:", file=sys.stderr)
            print("  python src/auth.py", file=sys.stderr)
            raise RuntimeError("tokenが見つかりません")

        # クライアントを初期化
        self.client = FreeeAPIClient(
            access_token=token_data["access_token"],
            company_id=self.company_id,
            base_url=self.base_url,
            on_token_refresh=self._refresh_token_callback,
        )

        return self.client

    async def run(self):
        """MCPサーバーを起動"""
        # ツールを登録
        register_tools(self.server, self.get_client)

        # stdio経由でサーバーを起動
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


def main():
    """メインエントリーポイント"""
    try:
        print("[freee] Starting MCP Server...", file=sys.stderr)
        server = FreeeMCPServer()
        print("[freee] Server initialized successfully", file=sys.stderr)
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("\n[freee] Server terminated by user", file=sys.stderr)
    except Exception as e:
        print(f"[freee] Fatal error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
