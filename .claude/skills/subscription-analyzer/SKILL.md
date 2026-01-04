---
name: subscription-analyzer
description: freee口座明細からサブスクリプションを分析。月額費用・年間コスト・解約候補を自動検出
version: 1.0.0
trigger: user-invoked
---

# サブスクリプション分析 Skill

freee MCPの`list_wallet_txns`を使用して、サブスクリプションを自動検出・分析します。

## 使用方法

```
/subscription-analyzer
```

## 実行手順

### 1. 口座一覧を取得
```
freee list_walletables を実行
→ credit_card タイプの口座IDを確認
```

### 2. 過去3ヶ月の明細を取得
```
freee list_wallet_txns を実行
- walletable_type: credit_card
- start_date: 3ヶ月前
- end_date: 今日
- entry_side: expense
```

### 3. サブスクを検出
patterns.yml のキーワードで明細をマッチング:
- `ANTHROPIC` → Claude
- `OPENAI` → ChatGPT
- `GITHUB` → GitHub
- etc.

### 4. レポート出力

```markdown
## サブスクリプション分析結果

### 概要
- 検出数: X件
- 月額合計: ¥XX,XXX
- 年間換算: ¥XXX,XXX

### 検出されたサービス
| サービス | カテゴリ | 月額 | 最終課金日 |
|---------|---------|------|-----------|
| Claude (API) | AI/ML | ¥7,200 | 2025-01-03 |
| GitHub | 開発 | ¥600 | 2025-01-01 |

### 解約候補
- [サービス名]: 重複/利用頻度低 等の理由
```

## 検出パターン

patterns.yml に80+サービスを定義済み:

| カテゴリ | 例 |
|---------|-----|
| AI/ML | ANTHROPIC, OPENAI, MIDJOURNEY, CURSOR |
| 開発ツール | GITHUB, VERCEL, SUPABASE, NEON |
| クラウド | AWS, GCP, AZURE, CLOUDFLARE |
| 生産性 | NOTION, FIGMA, SLACK, AIRTABLE |
| メディア | NETFLIX, SPOTIFY, YOUTUBE |

## 注意

- freee MCPが設定済みであること
- 明細テキスト形式はカード会社により異なる
