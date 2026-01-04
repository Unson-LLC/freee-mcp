"""Token暗号化保存・ロード機能"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional

from cryptography.fernet import Fernet


class TokenStore:
    """freee OAuth tokenの暗号化保存・ロード"""

    def __init__(self, encryption_key: str, token_file_path: Optional[str] = None):
        """
        Args:
            encryption_key: 32バイトのbase64エンコードされた暗号化キー
            token_file_path: token保存先パス（デフォルト: ~/.freee-mcp/tokens.enc）
        """
        self.cipher = Fernet(encryption_key.encode())
        self.token_file_path = Path(
            token_file_path or os.path.expanduser("~/.freee-mcp/tokens.enc")
        )
        self.token_file_path.parent.mkdir(parents=True, exist_ok=True)

    def save_token(self, token_data: Dict[str, str]) -> None:
        """
        tokenを暗号化して保存

        Args:
            token_data: {
                "access_token": "...",
                "refresh_token": "...",
                "expires_at": "1234567890",
                "token_type": "Bearer"
            }
        """
        json_bytes = json.dumps(token_data).encode()
        encrypted = self.cipher.encrypt(json_bytes)
        self.token_file_path.write_bytes(encrypted)

    def load_token(self) -> Optional[Dict[str, str]]:
        """
        保存されたtokenを復号化してロード

        Returns:
            token_data or None（ファイルが存在しない場合）
        """
        if not self.token_file_path.exists():
            return None

        try:
            encrypted = self.token_file_path.read_bytes()
            json_bytes = self.cipher.decrypt(encrypted)
            return json.loads(json_bytes.decode())
        except Exception as e:
            print(f"⚠️ token復号化エラー: {e}")
            return None

    def delete_token(self) -> None:
        """保存されたtokenを削除"""
        if self.token_file_path.exists():
            self.token_file_path.unlink()

    def has_token(self) -> bool:
        """tokenが保存されているか確認"""
        return self.token_file_path.exists()


def generate_encryption_key() -> str:
    """新しい暗号化キーを生成（セットアップ用）"""
    return Fernet.generate_key().decode()
