# freee MCP セットアップガイド

## 🎯 現在の状況

**✅ 完了:**
- Python MCPサーバーの実装（OAuth 2.0 PKCE対応）
- 既存 `freee_uploader.py` をベースにしたAPIクライアント
- token暗号化保存機能
- 依存パッケージのインストール

**📋 次のステップ:**
1. freee Developersでアプリ登録
2. 環境変数設定
3. 初回OAuth認証
4. Claude側MCP設定

---

## 1. freee Developersでアプリ登録

### 手順

1. **freee Developersにアクセス**
   https://developer.freee.co.jp/

2. **アプリケーションを作成**
   - アプリケーション名: `brainbase-freee-mcp`
   - 説明: `Claude MCP integration for brainbase`
   - リダイレクトURI: `http://localhost:8080/callback`

3. **必要なスコープを選択**
   - ✅ `read:companies` - 事業所情報の参照
   - ✅ `read:accounts` - 勘定科目の参照
   - ✅ `write:deals` - 取引の作成
   - ✅ `read:walletables` - 口座情報の参照
   - ✅ `write:receipts` - 証憑のアップロード

4. **CLIENT_IDとCLIENT_SECRETを取得**
   - アプリ詳細ページから確認
   - 安全に保管（後で使用）

---

## 2. 環境変数設定

### 2-1. 暗号化キーを生成

```bash
cd /Users/ksato/workspace/tools/freee-mcp
/Users/ksato/workspace/.venv/bin/python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

出力された文字列（例: `abc123...xyz`）をコピー

### 2-2. .envファイルを作成

```bash
cp .env.example .env
```

### 2-3. .envを編集

```bash
# freee OAuth 2.0 認証情報
FREEE_CLIENT_ID=your_client_id_from_freee_developers
FREEE_CLIENT_SECRET=your_client_secret_from_freee_developers
FREEE_REDIRECT_URI=http://localhost:8080/callback

# token暗号化キー（ステップ2-1で生成したもの）
TOKEN_ENCRYPTION_KEY=abc123...xyz

# freee API設定
FREEE_BASE_URL=https://api.freee.co.jp
FREEE_COMPANY_ID=your_company_id  # freeeの事業所IDを後で設定
```

### 2-4. workspace/.envに追加（オプション）

brainbase共通環境変数に追加する場合：

```bash
# /Users/ksato/workspace/.env に追記
echo "" >> /Users/ksato/workspace/.env
echo "# freee MCP" >> /Users/ksato/workspace/.env
echo "FREEE_CLIENT_ID=your_client_id" >> /Users/ksato/workspace/.env
echo "FREEE_CLIENT_SECRET=your_client_secret" >> /Users/ksato/workspace/.env
echo "TOKEN_ENCRYPTION_KEY=your_encryption_key" >> /Users/ksato/workspace/.env
```

---

## 3. 初回OAuth認証

### 3-1. 認証スクリプトを実行

```bash
cd /Users/ksato/workspace/tools/freee-mcp
/Users/ksato/workspace/.venv/bin/python src/auth.py
```

### 3-2. ブラウザで認証

1. ブラウザが自動で開き、freeeのログイン画面が表示される
2. freeeにログイン
3. アプリ連携を承認
4. 「Authorization successful!」と表示されたらOK
5. tokenが `~/.freee-mcp/tokens.enc` に暗号化保存される

### 3-3. 事業所IDを確認

```bash
/Users/ksato/workspace/.venv/bin/python -c "
import os
from dotenv import load_dotenv
from src.token_store import TokenStore
from src.freee_client import FreeeAPIClient

load_dotenv()
token_store = TokenStore(os.getenv('TOKEN_ENCRYPTION_KEY'))
token = token_store.load_token()
client = FreeeAPIClient(token['access_token'], 0)
companies = client.list_companies()
for c in companies:
    print(f\"事業所ID: {c['id']}, 名前: {c['name']}\")
"
```

出力された事業所IDを `.env` の `FREEE_COMPANY_ID` に設定

---

## 4. Claude側MCP設定

### 4-1. Claudeの設定ファイルを編集

```bash
# Linux/Mac
~/.config/Claude/claude_desktop_config.json

# Windows
%APPDATA%\Claude\claude_desktop_config.json
```

### 4-2. freee MCPサーバーを追加

```json
{
  "mcpServers": {
    "freee": {
      "command": "/Users/ksato/workspace/.venv/bin/python",
      "args": ["/Users/ksato/workspace/tools/freee-mcp/src/server.py"],
      "env": {
        "FREEE_CLIENT_ID": "your_client_id",
        "FREEE_CLIENT_SECRET": "your_client_secret",
        "TOKEN_ENCRYPTION_KEY": "your_encryption_key",
        "FREEE_COMPANY_ID": "your_company_id"
      }
    }
  }
}
```

### 4-3. Claudeを再起動

Claude Desktopアプリを再起動すると、freee MCPサーバーが利用可能になります。

---

## 5. 動作確認

Claudeで以下のように試してみてください：

```
freeeの事業所一覧を取得して
```

期待される結果：
```
事業所一覧:
[
  {
    "id": 1234567,
    "name": "合同会社雲孫",
    ...
  }
]
```

---

## 6. 利用可能なMCPツール

| ツール名 | 説明 | 例 |
|---------|------|-----|
| `list_companies` | 事業所一覧 | `freeeの事業所を確認` |
| `list_accounts` | 勘定科目一覧 | `freeeの勘定科目リストを取得` |
| `create_deal` | 取引作成 | `freeeに外注費10万円の取引を作成` |
| `list_walletables` | 口座一覧 | `freeeの口座情報を確認` |
| `upload_receipt` | 証憑アップロード | `この請求書PDFをfreeeにアップロード` |
| `get_partners` | 取引先一覧 | `freeeの取引先リストを取得` |

---

## トラブルシューティング

### token期限切れエラー

```bash
# tokenを削除して再認証
rm ~/.freee-mcp/tokens.enc
/Users/ksato/workspace/.venv/bin/python src/auth.py
```

### 環境変数が読み込まれない

```bash
# .envファイルの内容を確認
cat /Users/ksato/workspace/tools/freee-mcp/.env

# 環境変数を手動でexport
export FREEE_CLIENT_ID=your_client_id
export FREEE_CLIENT_SECRET=your_client_secret
export TOKEN_ENCRYPTION_KEY=your_key
```

### MCPサーバーが起動しない

```bash
# 直接実行してエラーを確認
cd /Users/ksato/workspace/tools/freee-mcp
/Users/ksato/workspace/.venv/bin/python src/server.py
```

---

## 次のステップ：Zeims × brainbase統合

このfreee MCPサーバーは、以下の統合の基盤です：

```
freee（実データ）
  ↓ freee MCP
brainbase（プロジェクト文脈・RACI・予算）
  ↓
Zeims（税務知識・仕訳提案）
  ↓
「この外注費、Zeimsプロジェクトの予算残25万円ですが大丈夫？」
```

杉山さんへのデモでは、この統合動作を見せることができます。
