#!/usr/bin/env /Users/ksato/workspace/.venv/bin/python
"""freee MCP 動作テスト"""

import sys
from pathlib import Path

# パスを追加
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
import os

# .envファイルを読み込み
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

from token_store import TokenStore
from freee_client import FreeeAPIClient

def test_freee_mcp():
    """freee MCP の動作テスト"""

    print("=" * 60)
    print("freee MCP 動作テスト")
    print("=" * 60)

    # 環境変数を確認
    print("\n✅ 環境変数:")
    print(f"  CLIENT_ID: {os.getenv('FREEE_CLIENT_ID')[:10]}...")
    print(f"  COMPANY_ID: {os.getenv('FREEE_COMPANY_ID')}")
    print(f"  TOKEN_ENCRYPTION_KEY: {os.getenv('TOKEN_ENCRYPTION_KEY')[:10]}...")

    # tokenを読み込み
    print("\n✅ tokenをロード中...")
    token_store = TokenStore(os.getenv('TOKEN_ENCRYPTION_KEY'))
    token_data = token_store.load_token()

    if not token_data:
        print("❌ tokenが見つかりません")
        return False

    print(f"  Access Token: {token_data['access_token'][:20]}...")

    # APIクライアントを初期化
    print("\n✅ freee APIクライアントを初期化中...")
    client = FreeeAPIClient(
        access_token=token_data['access_token'],
        company_id=int(os.getenv('FREEE_COMPANY_ID')),
    )

    # テスト1: 事業所一覧を取得
    print("\n📊 テスト1: 事業所一覧を取得")
    try:
        companies = client.list_companies()
        print(f"  ✅ 成功: {len(companies)}件の事業所を取得")
        for c in companies:
            print(f"     - {c['display_name']} (ID: {c['id']})")
    except Exception as e:
        print(f"  ❌ エラー: {e}")
        return False

    # テスト2: 勘定科目一覧を取得
    print("\n📊 テスト2: 勘定科目一覧を取得")
    try:
        accounts = client.list_accounts()
        print(f"  ✅ 成功: {len(accounts)}件の勘定科目を取得")
        # 最初の5件を表示
        for acc in accounts[:5]:
            print(f"     - {acc['name']} (ID: {acc['id']})")
        print(f"     ... (他 {len(accounts) - 5}件)")
    except Exception as e:
        print(f"  ❌ エラー: {e}")
        return False

    # テスト3: 口座一覧を取得
    print("\n📊 テスト3: 口座一覧を取得")
    try:
        walletables = client.list_walletables()
        print(f"  ✅ 成功: {len(walletables)}件の口座を取得")
        for w in walletables:
            print(f"     - {w['name']} (ID: {w['id']}, タイプ: {w['type']})")
    except Exception as e:
        print(f"  ❌ エラー: {e}")
        return False

    # テスト4: 取引先一覧を取得
    print("\n📊 テスト4: 取引先一覧を取得")
    try:
        partners = client.get_partners()
        print(f"  ✅ 成功: {len(partners)}件の取引先を取得")
        # 最初の5件を表示
        for p in partners[:5]:
            print(f"     - {p['name']} (ID: {p['id']})")
        if len(partners) > 5:
            print(f"     ... (他 {len(partners) - 5}件)")
    except Exception as e:
        print(f"  ❌ エラー: {e}")
        return False

    print("\n" + "=" * 60)
    print("🎉 すべてのテストが成功しました！")
    print("=" * 60)
    print("\n次のステップ:")
    print("  1. Claude Code でfreee MCPツールを使う")
    print("  2. Zeims × brainbase統合の準備")
    print("  3. 杉山さんへのデモ")

    return True


if __name__ == "__main__":
    success = test_freee_mcp()
    sys.exit(0 if success else 1)
