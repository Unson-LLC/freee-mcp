"""freee OAuth 2.0 PKCE認証フロー"""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Optional
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from dotenv import load_dotenv

# 絶対importに変更（スタンドアロン実行対応）
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from token_store import TokenStore

# .envファイルを明示的に読み込み
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


class FreeeOAuth:
    """freee OAuth 2.0 PKCE認証"""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://localhost:8080/callback",
        base_url: str = "https://accounts.secure.freee.co.jp",
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.base_url = base_url
        self.code_verifier: Optional[str] = None
        self.authorization_code: Optional[str] = None

    def generate_pkce_pair(self) -> tuple[str, str]:
        """
        PKCE用のcode_verifierとcode_challengeを生成

        Returns:
            (code_verifier, code_challenge)
        """
        # code_verifier: 43-128文字のランダム文字列（RFC 7636）
        code_verifier = secrets.token_urlsafe(64)[:128]

        # code_challenge: code_verifierのSHA256ハッシュをbase64urlエンコード
        challenge_bytes = hashlib.sha256(code_verifier.encode()).digest()
        code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('ascii').rstrip('=')

        return code_verifier, code_challenge

    def get_authorization_url(self) -> str:
        """
        認可URLを生成してブラウザで開く

        Returns:
            認可URL
        """
        self.code_verifier, code_challenge = self.generate_pkce_pair()

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "scope": "read write",
        }

        auth_url = f"{self.base_url}/public_api/authorize?{urlencode(params)}"
        return auth_url

    def start_callback_server(self) -> str:
        """
        ローカルサーバーを起動してコールバックを待機

        Returns:
            authorization_code
        """

        class CallbackHandler(BaseHTTPRequestHandler):
            oauth = self

            def do_GET(self_handler):
                """コールバックリクエストを処理"""
                parsed = urlparse(self_handler.path)
                query = parse_qs(parsed.query)

                if "code" in query:
                    self.authorization_code = query["code"][0]
                    self_handler.send_response(200)
                    self_handler.send_header("Content-type", "text/html")
                    self_handler.end_headers()
                    self_handler.wfile.write(
                        b"<html><body><h1>Authorization successful!</h1>"
                        b"<p>You can close this window now.</p></body></html>"
                    )
                else:
                    self_handler.send_response(400)
                    self_handler.send_header("Content-type", "text/html")
                    self_handler.end_headers()
                    self_handler.wfile.write(b"<html><body><h1>Error: No code received</h1></body></html>")

            def log_message(self_handler, format, *args):
                """ログを抑制"""
                pass

        # ポート8080でサーバー起動
        server = HTTPServer(("localhost", 8080), CallbackHandler)
        print("🌐 ローカルサーバーを起動しました（http://localhost:8080）")
        print("📱 ブラウザで認証を完了してください...")

        # 1回のリクエストを待機
        server.handle_request()
        server.server_close()

        if not self.authorization_code:
            raise RuntimeError("認可コードを取得できませんでした")

        return self.authorization_code

    def exchange_code_for_token(self, authorization_code: str) -> Dict[str, str]:
        """
        認可コードをアクセストークンと交換

        Args:
            authorization_code: freeeから取得した認可コード

        Returns:
            {
                "access_token": "...",
                "refresh_token": "...",
                "expires_in": 3600,
                "token_type": "Bearer"
            }
        """
        token_url = f"{self.base_url}/public_api/token"

        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": authorization_code,
            "redirect_uri": self.redirect_uri,
            "code_verifier": self.code_verifier,
        }

        resp = requests.post(token_url, data=data)
        if resp.status_code != 200:
            raise RuntimeError(f"Token交換エラー: {resp.status_code} {resp.text}")

        token_data = resp.json()
        # expires_atを計算
        token_data["expires_at"] = int(time.time()) + token_data.get("expires_in", 3600)
        return token_data

    def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """
        リフレッシュトークンで新しいアクセストークンを取得

        Args:
            refresh_token: 保存されているリフレッシュトークン

        Returns:
            新しいtoken_data
        """
        token_url = f"{self.base_url}/public_api/token"

        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
        }

        resp = requests.post(token_url, data=data)
        if resp.status_code != 200:
            raise RuntimeError(f"Token更新エラー: {resp.status_code} {resp.text}")

        token_data = resp.json()
        token_data["expires_at"] = int(time.time()) + token_data.get("expires_in", 3600)
        return token_data


def authenticate() -> Dict[str, str]:
    """
    初回認証フロー（CLIから実行）

    Returns:
        token_data
    """
    client_id = os.getenv("FREEE_CLIENT_ID")
    client_secret = os.getenv("FREEE_CLIENT_SECRET")
    redirect_uri = os.getenv("FREEE_REDIRECT_URI", "http://localhost:8080/callback")
    encryption_key = os.getenv("TOKEN_ENCRYPTION_KEY")

    if not all([client_id, client_secret, encryption_key]):
        raise RuntimeError(
            "環境変数が不足しています: FREEE_CLIENT_ID, FREEE_CLIENT_SECRET, TOKEN_ENCRYPTION_KEY"
        )

    oauth = FreeeOAuth(client_id, client_secret, redirect_uri)
    token_store = TokenStore(encryption_key)

    # 既存tokenがあるかチェック
    if token_store.has_token():
        print("✅ 既存のtokenが見つかりました")
        token_data = token_store.load_token()
        if token_data and token_data.get("expires_at", 0) > time.time():
            print("✅ tokenは有効です")
            return token_data
        elif token_data and token_data.get("refresh_token"):
            print("🔄 tokenをリフレッシュします...")
            try:
                new_token = oauth.refresh_access_token(token_data["refresh_token"])
                token_store.save_token(new_token)
                print("✅ tokenを更新しました")
                return new_token
            except Exception as e:
                print(f"⚠️ リフレッシュ失敗: {e}")
                print("新規認証を開始します...")

    # 新規認証
    print("=" * 60)
    print("freee OAuth 2.0 PKCE 認証")
    print("=" * 60)

    auth_url = oauth.get_authorization_url()
    print(f"\n認可URL: {auth_url}\n")

    # ブラウザを開く
    webbrowser.open(auth_url)

    # コールバックを待機
    authorization_code = oauth.start_callback_server()

    # tokenを取得
    print("\n🔑 アクセストークンを取得中...")
    token_data = oauth.exchange_code_for_token(authorization_code)

    # 暗号化して保存
    token_store.save_token(token_data)
    print(f"✅ tokenを保存しました: {token_store.token_file_path}")

    return token_data


if __name__ == "__main__":
    # CLI実行: 初回認証
    try:
        token = authenticate()
        print("\n🎉 認証完了！")
        print(f"Access Token: {token['access_token'][:20]}...")
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        exit(1)
