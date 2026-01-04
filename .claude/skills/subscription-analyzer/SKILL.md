---
name: subscription-analyzer
description: freee口座明細からサブスクリプションを分析。月額費用・年間コスト・解約候補を自動検出し、コスト削減提案を行う
version: 1.0.0
trigger: user-invoked
---

# サブスクリプション分析 Skill

freee MCPの`list_wallet_txns`を使用して、クレジットカード・口座明細からサブスクリプションサービスを自動検出・分析します。

## 使用方法

```
/subscription-analyzer
```

または会話内で:
```
サブスクリプションを分析して
月額課金を確認して
無駄なサブスクを見つけて
```

## 分析フロー

### Phase 1: データ収集
1. `list_walletables` で口座一覧を取得
2. `list_wallet_txns` で過去3ヶ月の明細を取得（クレジットカード中心）

### Phase 2: パターン検出
以下のパターンでサブスクリプションを検出:

| パターン | 例 |
|---------|-----|
| SaaS/クラウド | ANTHROPIC, OPENAI, AWS, GOOGLE CLOUD, AZURE |
| 開発ツール | GITHUB, NOTION, FIGMA, SLACK, VERCEL |
| AI/ML | MIDJOURNEY, RUNWAY, CURSOR, COPILOT |
| メディア | NETFLIX, SPOTIFY, YOUTUBE, APPLE |
| ビジネス | ZOOM, DOCUSIGN, HUBSPOT, SALESFORCE |
| その他定期課金 | 月次で同一金額が発生するもの |

### Phase 3: 分析レポート生成

出力フォーマット:
```markdown
## サブスクリプション分析レポート

### 概要
- 検出されたサブスク数: X件
- 月額合計: ¥XX,XXX
- 年間合計: ¥XXX,XXX

### カテゴリ別内訳
| カテゴリ | 件数 | 月額計 |
|---------|------|--------|
| AI/ML | 3 | ¥15,000 |
| 開発ツール | 2 | ¥5,000 |
| ... | ... | ... |

### 検出されたサブスクリプション
| サービス名 | 月額 | 最終課金日 | カード |
|-----------|------|-----------|--------|
| ANTHROPIC | ¥7,200 | 2025-01-03 | Upsider |
| ... | ... | ... | ... |

### コスト削減候補
- [サービス名]: 理由
```

## 検出ロジック

### サービス名の正規化
明細テキストからサービス名を抽出:
- `ANTHROPIC_カード13` → `ANTHROPIC`
- `OPENAI *CHATGPT` → `OPENAI`
- `GITHUB.COM` → `GITHUB`

### 重複課金検出
- 同一サービスで複数課金がある場合にアラート
- 例: ChatGPT Plus × 2アカウント

### 利用頻度との相関（オプション）
- 高額だが利用頻度が低いサービスを解約候補として提案

## 設定

環境変数（オプション）:
```
SUBSCRIPTION_ANALYSIS_MONTHS=3  # 分析対象期間（月）
```

## 注意事項

- freee MCPが設定済みであることが前提
- `list_wallet_txns` ツールへのアクセス権が必要
- 明細テキストの形式はカード会社により異なる

## 実装例

```python
# 1. 口座一覧を取得
walletables = await freee.list_walletables()

# 2. クレジットカードの明細を取得
for wallet in walletables:
    if wallet["type"] == "credit_card":
        txns = await freee.list_wallet_txns(
            walletable_id=wallet["id"],
            start_date="2024-10-01",
            end_date="2025-01-04",
            entry_side="expense"
        )

# 3. サブスクパターンをマッチング
subscriptions = detect_subscriptions(txns)

# 4. レポート生成
report = generate_report(subscriptions)
```
