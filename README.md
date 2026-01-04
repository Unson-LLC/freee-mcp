# freee MCP Server

freee会計APIとClaude MCPを連携するサーバー。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)

## 概要

- **目的**: Claudeからfreee会計データを操作（取引作成・口座確認・証憑アップロード・財務諸表取得等）
- **認証**: OAuth 2.0 PKCE（ブラウザ認証）
- **token管理**: 暗号化保存 + 自動リフレッシュ
- **実装言語**: Python 3.13+

## 機能

### MCPツール

| ツール名 | 説明 | freee API |
|---------|------|-----|
| `list_companies` | 事業所一覧取得 | GET /api/1/companies |
| `list_accounts` | 勘定科目一覧 | GET /api/1/account_items |
| `list_walletables` | 口座一覧 | GET /api/1/walletables |
| `list_wallet_txns` | 口座明細一覧（元明細テキスト含む） | GET /api/1/wallet_txns |
| `list_deals` | 取引一覧 | GET /api/1/deals |
| `list_invoices` | 請求書一覧 | GET /api/1/invoices |
| `get_partners` | 取引先一覧 | GET /api/1/partners |
| `create_deal` | 取引作成 | POST /api/1/deals |
| `upload_receipt` | 証憑アップロード | POST /api/1/receipts |
| `get_trial_balance_bs` | 貸借対照表（BS） | GET /api/1/reports/trial_bs |
| `get_trial_balance_pl` | 損益計算書（PL） | GET /api/1/reports/trial_pl |

### OAuth 2.0 PKCE認証フロー

```
1. ブラウザで認証URL起動
2. freeeログイン → 認可コード取得
3. アクセストークン取得 → 暗号化保存
4. リフレッシュトークンで自動更新
```

## セットアップ

### 1. freee Developersでアプリ登録

https://developer.freee.co.jp/

- アプリケーション名: 任意（例: `freee-mcp-server`）
- リダイレクトURI: `http://localhost:8080/callback`
- 必要なスコープ:
  - `read:companies` - 事業所情報
  - `read:accounts` - 勘定科目
  - `read:walletables` - 口座情報
  - `read:wallet_txns` - 口座明細
  - `read:deals` - 取引参照
  - `write:deals` - 取引作成
  - `read:invoices` - 請求書参照
  - `read:partners` - 取引先参照
  - `write:receipts` - 証憑アップロード
  - `read:reports` - 財務諸表

CLIENT_ID と CLIENT_SECRET を取得してください。

### 2. 環境変数設定

```bash
cp .env.example .env
# .env を編集
```

```.env
FREEE_CLIENT_ID=your_client_id
FREEE_CLIENT_SECRET=your_client_secret
FREEE_REDIRECT_URI=http://localhost:8080/callback
TOKEN_ENCRYPTION_KEY=generate_random_32_bytes
FREEE_COMPANY_ID=your_company_id
```

暗号化キーの生成:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. 依存関係のインストール

```bash
pip install -e .
```

### 4. 初回認証

```bash
python src/auth.py
```

ブラウザが開き、freeeログイン → tokenが `~/.freee-mcp/tokens.enc` に保存されます。

### 5. MCPサーバー起動

```bash
python src/server.py
```

### 6. Claude側設定

Claude Desktop の `claude_desktop_config.json` または Claude Code の `.mcp.json`:

```json
{
  "mcpServers": {
    "freee": {
      "command": "python",
      "args": ["/path/to/freee-mcp/src/server.py"],
      "env": {
        "FREEE_CLIENT_ID": "your_client_id",
        "FREEE_CLIENT_SECRET": "your_client_secret",
        "FREEE_COMPANY_ID": "your_company_id",
        "TOKEN_ENCRYPTION_KEY": "your_encryption_key"
      }
    }
  }
}
```

## Claude Code Skills

Claude Codeで使える便利なSkillを同梱しています。

### subscription-analyzer

口座明細からサブスクリプションを自動検出・分析します。

```
/subscription-analyzer
```

**機能:**
- 80+サービスの自動検出（AI/ML, 開発ツール, クラウド等）
- カテゴリ別コスト集計
- 重複課金・解約候補の提案

**検出対象例:**
| カテゴリ | サービス |
|---------|---------|
| AI/ML | ANTHROPIC, OPENAI, MIDJOURNEY, CURSOR |
| クラウド | AWS, GCP, AZURE, VERCEL, FLY.IO |
| 開発ツール | GITHUB, NEON, SUPABASE, UPSTASH |
| 生産性 | NOTION, SLACK, ASANA, FIGMA |

詳細: [.claude/skills/subscription-analyzer/SKILL.md](.claude/skills/subscription-analyzer/SKILL.md)

## ディレクトリ構成

```
freee-mcp/
├── README.md
├── SETUP.md           # 詳細セットアップガイド
├── LICENSE
├── pyproject.toml
├── .env.example
├── src/
│   ├── __init__.py
│   ├── server.py          # MCPサーバーのメイン
│   ├── auth.py            # OAuth 2.0 PKCE認証
│   ├── token_store.py     # トークン暗号化保存
│   ├── freee_client.py    # freee APIクライアント
│   └── tools.py           # MCPツール定義
├── .claude/skills/
│   └── subscription-analyzer/  # サブスク分析Skill
│       ├── SKILL.md
│       └── patterns.yml
└── tests/
    └── test_integration.py
```

## 使用例

### 口座明細の取得（サブスク分析に便利）

```
Claude: freeeの口座明細を取得して、サブスクリプションを確認して
```

→ `list_wallet_txns` で明細テキスト（例: "ANTHROPIC_カード13"）を含む明細を取得

### 財務諸表の確認

```
Claude: 2024年度の損益計算書を見せて
```

→ `get_trial_balance_pl` で損益計算書を取得

### 取引の作成

```
Claude: 今日付けで外注費30,000円の取引を作成して
```

→ `create_deal` で取引を自動作成

## 技術仕様

### token暗号化

- **暗号化方式**: Fernet（symmetric encryption）
- **保存場所**: `~/.freee-mcp/tokens.enc`
- **キー管理**: 環境変数 `TOKEN_ENCRYPTION_KEY`（32 bytes）

### エラーハンドリング

- **401 Unauthorized**: 自動リフレッシュ → 再実行
- **429 Too Many Requests**: 指数バックオフ（2^n秒）
- **500 Server Error**: 3回リトライ

## ライセンス

MIT License - 詳細は [LICENSE](./LICENSE) を参照

## 貢献

Issue・Pull Request歓迎です。

## 関連リンク

- [freee API ドキュメント](https://developer.freee.co.jp/docs)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Claude Code](https://claude.ai/code)
