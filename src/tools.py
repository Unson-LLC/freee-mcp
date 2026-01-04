"""freee MCP ツール定義"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from mcp.server import Server
from mcp.types import Tool, TextContent

# 絶対importに変更（スタンドアロン実行対応）
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from freee_client import FreeeAPIClient


def register_tools(server: Server, get_client: callable) -> None:
    """
    MCPツールをサーバーに登録

    Args:
        server: MCPサーバーインスタンス
        get_client: FreeeAPIClientを取得する関数
    """

    # ========== list_companies ==========

    @server.list_tools()
    async def list_tools() -> List[Tool]:
        return [
            Tool(
                name="list_companies",
                description="freee事業所一覧を取得",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="list_accounts",
                description="勘定科目一覧を取得",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "company_id": {
                            "type": "integer",
                            "description": "事業所ID（省略時はデフォルト）",
                        }
                    },
                },
            ),
            Tool(
                name="create_deal",
                description="freee取引を作成",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "issue_date": {
                            "type": "string",
                            "description": "発生日（YYYY-MM-DD形式）",
                        },
                        "deal_type": {
                            "type": "string",
                            "enum": ["income", "expense"],
                            "description": "取引タイプ（income: 収入, expense: 支出）",
                        },
                        "details": {
                            "type": "array",
                            "description": "明細リスト",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "account_item_id": {"type": "integer"},
                                    "tax_code": {"type": "integer"},
                                    "amount": {"type": "integer"},
                                    "item_id": {"type": "integer"},
                                    "description": {"type": "string"},
                                },
                                "required": ["account_item_id", "tax_code", "amount"],
                            },
                        },
                        "company_id": {
                            "type": "integer",
                            "description": "事業所ID（省略時はデフォルト）",
                        },
                        "description": {
                            "type": "string",
                            "description": "取引の説明",
                        },
                    },
                    "required": ["issue_date", "deal_type", "details"],
                },
            ),
            Tool(
                name="list_walletables",
                description="freee口座一覧を取得",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "company_id": {
                            "type": "integer",
                            "description": "事業所ID（省略時はデフォルト）",
                        }
                    },
                },
            ),
            Tool(
                name="upload_receipt",
                description="証憑（レシート・請求書）をfreeeにアップロード",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "アップロードするファイルのパス",
                        },
                        "company_id": {
                            "type": "integer",
                            "description": "事業所ID（省略時はデフォルト）",
                        },
                        "description": {
                            "type": "string",
                            "description": "証憑の説明",
                        },
                    },
                    "required": ["file_path"],
                },
            ),
            Tool(
                name="get_partners",
                description="freee取引先一覧を取得",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "company_id": {
                            "type": "integer",
                            "description": "事業所ID（省略時はデフォルト）",
                        }
                    },
                },
            ),
            Tool(
                name="list_deals",
                description="freee取引一覧を取得",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "company_id": {
                            "type": "integer",
                            "description": "事業所ID（省略時はデフォルト）",
                        },
                        "account_item_id": {
                            "type": "integer",
                            "description": "勘定科目IDで絞り込み",
                        },
                        "partner_id": {
                            "type": "integer",
                            "description": "取引先IDで絞り込み",
                        },
                        "start_issue_date": {
                            "type": "string",
                            "description": "開始日（YYYY-MM-DD形式）",
                        },
                        "end_issue_date": {
                            "type": "string",
                            "description": "終了日（YYYY-MM-DD形式）",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "取得件数（最大100、デフォルト100）",
                        },
                    },
                },
            ),
            Tool(
                name="list_invoices",
                description="freee請求書一覧を取得",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "company_id": {
                            "type": "integer",
                            "description": "事業所ID（省略時はデフォルト）",
                        },
                        "partner_id": {
                            "type": "integer",
                            "description": "取引先IDで絞り込み",
                        },
                        "issue_date_min": {
                            "type": "string",
                            "description": "発行日の開始日（YYYY-MM-DD形式）",
                        },
                        "issue_date_max": {
                            "type": "string",
                            "description": "発行日の終了日（YYYY-MM-DD形式）",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "取得件数（最大100、デフォルト100）",
                        },
                    },
                },
            ),
            Tool(
                name="get_trial_balance_bs",
                description="試算表（貸借対照表：BS）を取得",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "fiscal_year": {
                            "type": "integer",
                            "description": "会計年度",
                        },
                        "company_id": {
                            "type": "integer",
                            "description": "事業所ID（省略時はデフォルト）",
                        },
                        "start_month": {
                            "type": "integer",
                            "description": "開始会計月（1-12）、省略時は期首",
                            "minimum": 1,
                            "maximum": 12,
                        },
                        "end_month": {
                            "type": "integer",
                            "description": "終了会計月（1-12）、省略時は期末",
                            "minimum": 1,
                            "maximum": 12,
                        },
                    },
                    "required": ["fiscal_year"],
                },
            ),
            Tool(
                name="get_trial_balance_pl",
                description="試算表（損益計算書：PL）を取得",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "fiscal_year": {
                            "type": "integer",
                            "description": "会計年度",
                        },
                        "company_id": {
                            "type": "integer",
                            "description": "事業所ID（省略時はデフォルト）",
                        },
                        "start_month": {
                            "type": "integer",
                            "description": "開始会計月（1-12）、省略時は期首",
                            "minimum": 1,
                            "maximum": 12,
                        },
                        "end_month": {
                            "type": "integer",
                            "description": "終了会計月（1-12）、省略時は期末",
                            "minimum": 1,
                            "maximum": 12,
                        },
                    },
                    "required": ["fiscal_year"],
                },
            ),
            Tool(
                name="list_wallet_txns",
                description="freee口座明細一覧を取得。descriptionフィールドに元明細テキスト（ANTHROPIC等）が含まれる",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "company_id": {
                            "type": "integer",
                            "description": "事業所ID（省略時はデフォルト）",
                        },
                        "walletable_type": {
                            "type": "string",
                            "enum": ["bank_account", "credit_card", "wallet"],
                            "description": "口座種別（bank_account, credit_card, wallet）",
                        },
                        "walletable_id": {
                            "type": "integer",
                            "description": "口座ID（絞り込み用）",
                        },
                        "start_date": {
                            "type": "string",
                            "description": "開始日（YYYY-MM-DD形式）",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "終了日（YYYY-MM-DD形式）",
                        },
                        "entry_side": {
                            "type": "string",
                            "enum": ["income", "expense"],
                            "description": "入出金区分（income: 入金, expense: 出金）",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "取得件数（最大100、デフォルト100）",
                        },
                    },
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """ツール実行"""
        client = get_client()

        try:
            if name == "list_companies":
                companies = client.list_companies()
                return [
                    TextContent(
                        type="text",
                        text=f"事業所一覧:\n{format_json(companies)}",
                    )
                ]

            elif name == "list_accounts":
                company_id = arguments.get("company_id")
                accounts = client.list_accounts(company_id)
                return [
                    TextContent(
                        type="text",
                        text=f"勘定科目一覧:\n{format_json(accounts)}",
                    )
                ]

            elif name == "create_deal":
                result = client.create_deal(
                    issue_date=arguments["issue_date"],
                    deal_type=arguments["deal_type"],
                    details=arguments["details"],
                    company_id=arguments.get("company_id"),
                    description=arguments.get("description"),
                )
                return [
                    TextContent(
                        type="text",
                        text=f"取引を作成しました:\n{format_json(result)}",
                    )
                ]

            elif name == "list_walletables":
                company_id = arguments.get("company_id")
                walletables = client.list_walletables(company_id)
                return [
                    TextContent(
                        type="text",
                        text=f"口座一覧:\n{format_json(walletables)}",
                    )
                ]

            elif name == "upload_receipt":
                file_path = Path(arguments["file_path"])
                if not file_path.exists():
                    return [
                        TextContent(
                            type="text",
                            text=f"❌ ファイルが見つかりません: {file_path}",
                        )
                    ]

                result = client.upload_receipt(
                    file_path=file_path,
                    company_id=arguments.get("company_id"),
                    description=arguments.get("description"),
                )
                return [
                    TextContent(
                        type="text",
                        text=f"証憑をアップロードしました:\n{format_json(result)}",
                    )
                ]

            elif name == "get_partners":
                company_id = arguments.get("company_id")
                partners = client.get_partners(company_id)
                return [
                    TextContent(
                        type="text",
                        text=f"取引先一覧:\n{format_json(partners)}",
                    )
                ]

            elif name == "list_deals":
                deals = client.list_deals(
                    company_id=arguments.get("company_id"),
                    account_item_id=arguments.get("account_item_id"),
                    partner_id=arguments.get("partner_id"),
                    start_issue_date=arguments.get("start_issue_date"),
                    end_issue_date=arguments.get("end_issue_date"),
                    limit=arguments.get("limit", 100),
                )
                return [
                    TextContent(
                        type="text",
                        text=f"取引一覧:\n{format_json(deals)}",
                    )
                ]

            elif name == "list_invoices":
                invoices = client.list_invoices(
                    company_id=arguments.get("company_id"),
                    partner_id=arguments.get("partner_id"),
                    issue_date_min=arguments.get("issue_date_min"),
                    issue_date_max=arguments.get("issue_date_max"),
                    limit=arguments.get("limit", 100),
                )
                return [
                    TextContent(
                        type="text",
                        text=f"請求書一覧:\n{format_json(invoices)}",
                    )
                ]

            elif name == "get_trial_balance_bs":
                result = client.get_trial_balance_bs(
                    fiscal_year=arguments["fiscal_year"],
                    company_id=arguments.get("company_id"),
                    start_month=arguments.get("start_month"),
                    end_month=arguments.get("end_month"),
                )
                return [
                    TextContent(
                        type="text",
                        text=f"貸借対照表（BS）:\n{format_json(result)}",
                    )
                ]

            elif name == "get_trial_balance_pl":
                result = client.get_trial_balance_pl(
                    fiscal_year=arguments["fiscal_year"],
                    company_id=arguments.get("company_id"),
                    start_month=arguments.get("start_month"),
                    end_month=arguments.get("end_month"),
                )
                return [
                    TextContent(
                        type="text",
                        text=f"損益計算書（PL）:\n{format_json(result)}",
                    )
                ]

            elif name == "list_wallet_txns":
                wallet_txns = client.list_wallet_txns(
                    company_id=arguments.get("company_id"),
                    walletable_type=arguments.get("walletable_type"),
                    walletable_id=arguments.get("walletable_id"),
                    start_date=arguments.get("start_date"),
                    end_date=arguments.get("end_date"),
                    entry_side=arguments.get("entry_side"),
                    limit=arguments.get("limit", 100),
                )
                return [
                    TextContent(
                        type="text",
                        text=f"口座明細一覧:\n{format_json(wallet_txns)}",
                    )
                ]

            else:
                return [
                    TextContent(
                        type="text",
                        text=f"❌ 不明なツール: {name}",
                    )
                ]

        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=f"❌ エラー: {str(e)}",
                )
            ]


def format_json(data: Any) -> str:
    """JSONデータを見やすく整形"""
    import json

    return json.dumps(data, ensure_ascii=False, indent=2)
