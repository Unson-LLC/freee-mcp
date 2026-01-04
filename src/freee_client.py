"""freee API クライアント（既存 freee_uploader.py ベース）"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, List, Optional

import requests


class FreeeAPIClient:
    """freee API クライアント（自動リトライ・リフレッシュ対応）"""

    def __init__(
        self,
        access_token: str,
        company_id: int,
        base_url: str = "https://api.freee.co.jp",
        on_token_refresh: Optional[callable] = None,
    ):
        """
        Args:
            access_token: freee APIアクセストークン
            company_id: 事業所ID
            base_url: freee API ベースURL
            on_token_refresh: token更新時のコールバック（新しいtokenを保存する）
        """
        self.access_token = access_token
        self.company_id = company_id
        self.base_url = base_url
        self.on_token_refresh = on_token_refresh

    def _get_headers(self) -> Dict[str, str]:
        """共通リクエストヘッダー"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        max_retries: int = 3,
        **kwargs,
    ) -> requests.Response:
        """
        リトライ・レート制限対応付きリクエスト

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/api/1/companies")
            max_retries: 最大リトライ回数
            **kwargs: requests.request() に渡す追加パラメータ

        Returns:
            Response object
        """
        url = f"{self.base_url}{endpoint}"
        headers = kwargs.pop("headers", {})
        headers.update(self._get_headers())

        for attempt in range(max_retries):
            resp = requests.request(method, url, headers=headers, **kwargs)

            # 成功
            if resp.status_code in (200, 201):
                return resp

            # 401: token期限切れ → リフレッシュ（コールバックがあれば）
            if resp.status_code == 401:
                if self.on_token_refresh:
                    print("🔄 tokenをリフレッシュします...")
                    new_token = self.on_token_refresh()
                    self.access_token = new_token["access_token"]
                    headers.update(self._get_headers())
                    continue
                else:
                    raise RuntimeError(f"401 Unauthorized: token期限切れ {resp.text}")

            # 429: レート制限 → 指数バックオフ
            if resp.status_code == 429:
                wait_time = 2**attempt
                print(f"⏳ レート制限（429）: {wait_time}秒待機...")
                time.sleep(wait_time)
                continue

            # 500系エラー → リトライ
            if 500 <= resp.status_code < 600:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    print(f"⚠️ サーバーエラー（{resp.status_code}）: {wait_time}秒後にリトライ...")
                    time.sleep(wait_time)
                    continue

            # その他エラー
            raise RuntimeError(
                f"freee API エラー: {resp.status_code} {resp.text}"
            )

        raise RuntimeError(f"最大リトライ回数（{max_retries}）を超えました")

    # ========== 事業所 ==========

    def list_companies(self) -> List[Dict]:
        """
        事業所一覧を取得

        Returns:
            [{"id": 123, "name": "合同会社雲孫", ...}, ...]
        """
        resp = self._request_with_retry("GET", "/api/1/companies")
        return resp.json().get("companies", [])

    # ========== 勘定科目 ==========

    def list_accounts(self, company_id: Optional[int] = None) -> List[Dict]:
        """
        勘定科目一覧を取得

        Args:
            company_id: 事業所ID（省略時はデフォルト）

        Returns:
            [{"id": 1, "name": "現金", ...}, ...]
        """
        cid = company_id or self.company_id
        resp = self._request_with_retry("GET", f"/api/1/account_items?company_id={cid}")
        return resp.json().get("account_items", [])

    # ========== 取引 ==========

    def create_deal(
        self,
        issue_date: str,
        deal_type: str,  # "income" or "expense"
        details: List[Dict],
        company_id: Optional[int] = None,
        **kwargs,
    ) -> Dict:
        """
        取引を作成

        Args:
            issue_date: 発生日（YYYY-MM-DD）
            deal_type: "income"（収入） or "expense"（支出）
            details: 明細リスト [{"account_item_id": 1, "amount": 1000, ...}, ...]
            company_id: 事業所ID（省略時はデフォルト）
            **kwargs: その他パラメータ（ref_number, description, etc.）

        Returns:
            {"deal": {"id": 123, ...}}
        """
        cid = company_id or self.company_id
        payload = {
            "company_id": cid,
            "issue_date": issue_date,
            "type": deal_type,
            "details": details,
            **kwargs,
        }
        resp = self._request_with_retry("POST", "/api/1/deals", json=payload)
        return resp.json()

    # ========== 口座 ==========

    def list_walletables(self, company_id: Optional[int] = None) -> List[Dict]:
        """
        口座一覧を取得

        Args:
            company_id: 事業所ID（省略時はデフォルト）

        Returns:
            [{"id": 1, "name": "現金", "type": "bank_account", ...}, ...]
        """
        cid = company_id or self.company_id
        resp = self._request_with_retry("GET", f"/api/1/walletables?company_id={cid}")
        return resp.json().get("walletables", [])

    # ========== 証憑（レシート・請求書） ==========

    def upload_receipt(
        self,
        file_path: Path,
        company_id: Optional[int] = None,
        description: Optional[str] = None,
    ) -> Dict:
        """
        証憑ファイルをアップロード

        Args:
            file_path: アップロードするファイルのパス
            company_id: 事業所ID（省略時はデフォルト）
            description: 説明（オプション）

        Returns:
            {"receipt": {"id": 123, ...}}
        """
        cid = company_id or self.company_id
        url = f"{self.base_url}/api/1/receipts"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        with open(file_path, "rb") as f:
            files = {"receipt": (file_path.name, f, "application/pdf")}
            data = {"company_id": cid}
            if description:
                data["description"] = description

            resp = requests.post(url, headers=headers, files=files, data=data)

        if resp.status_code not in (200, 201):
            raise RuntimeError(f"証憑アップロードエラー: {resp.status_code} {resp.text}")

        return resp.json()

    # ========== その他 ==========

    def get_partners(self, company_id: Optional[int] = None) -> List[Dict]:
        """
        取引先一覧を取得

        Args:
            company_id: 事業所ID（省略時はデフォルト）

        Returns:
            [{"id": 1, "name": "株式会社〇〇", ...}, ...]
        """
        cid = company_id or self.company_id
        resp = self._request_with_retry("GET", f"/api/1/partners?company_id={cid}")
        return resp.json().get("partners", [])

    # ========== 取引 ==========

    def list_deals(
        self,
        company_id: Optional[int] = None,
        account_item_id: Optional[int] = None,
        partner_id: Optional[int] = None,
        start_issue_date: Optional[str] = None,
        end_issue_date: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """
        取引一覧を取得

        Args:
            company_id: 事業所ID（省略時はデフォルト）
            account_item_id: 勘定科目ID（絞り込み用）
            partner_id: 取引先ID（絞り込み用）
            start_issue_date: 開始日（YYYY-MM-DD）
            end_issue_date: 終了日（YYYY-MM-DD）
            limit: 取得件数（最大100）

        Returns:
            [{"id": 123, "issue_date": "2025-01-01", "details": [...], ...}, ...]
        """
        cid = company_id or self.company_id
        params = {
            "company_id": cid,
            "limit": limit,
        }
        if account_item_id:
            params["account_item_id"] = account_item_id
        if partner_id:
            params["partner_id"] = partner_id
        if start_issue_date:
            params["start_issue_date"] = start_issue_date
        if end_issue_date:
            params["end_issue_date"] = end_issue_date

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        resp = self._request_with_retry("GET", f"/api/1/deals?{query_string}")
        return resp.json().get("deals", [])

    # ========== ウォレット取引（明細） ==========

    def list_wallet_txns(
        self,
        company_id: Optional[int] = None,
        walletable_type: Optional[str] = None,
        walletable_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        entry_side: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """
        ウォレット取引（明細）一覧を取得

        Args:
            company_id: 事業所ID（省略時はデフォルト）
            walletable_type: 口座種別（"bank_account", "credit_card", "wallet"）
            walletable_id: 口座ID（絞り込み用）
            start_date: 開始日（YYYY-MM-DD）
            end_date: 終了日（YYYY-MM-DD）
            entry_side: 入出金区分（"income" or "expense"）
            limit: 取得件数（最大100）

        Returns:
            [{"id": 123, "date": "2025-01-01", "amount": 10000,
              "description": "ANTHROPIC_カード13", ...}, ...]
        """
        cid = company_id or self.company_id
        params = {
            "company_id": cid,
            "limit": limit,
        }
        if walletable_type:
            params["walletable_type"] = walletable_type
        if walletable_id:
            params["walletable_id"] = walletable_id
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if entry_side:
            params["entry_side"] = entry_side

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        resp = self._request_with_retry("GET", f"/api/1/wallet_txns?{query_string}")
        return resp.json().get("wallet_txns", [])

    # ========== 請求書 ==========

    def list_invoices(
        self,
        company_id: Optional[int] = None,
        partner_id: Optional[int] = None,
        issue_date_min: Optional[str] = None,
        issue_date_max: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """
        請求書一覧を取得

        Args:
            company_id: 事業所ID（省略時はデフォルト）
            partner_id: 取引先ID（絞り込み用）
            issue_date_min: 発行日の開始日（YYYY-MM-DD）
            issue_date_max: 発行日の終了日（YYYY-MM-DD）
            limit: 取得件数（最大100）

        Returns:
            [{"id": 123, "invoice_number": "INV-001", "partner_name": "株式会社〇〇", "total_amount": 10000, ...}, ...]
        """
        cid = company_id or self.company_id
        params = {
            "company_id": cid,
            "limit": limit,
        }
        if partner_id:
            params["partner_id"] = partner_id
        if issue_date_min:
            params["issue_date_min"] = issue_date_min
        if issue_date_max:
            params["issue_date_max"] = issue_date_max

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        resp = self._request_with_retry("GET", f"/api/1/invoices?{query_string}")
        return resp.json().get("invoices", [])

    # ========== レポート（財務諸表） ==========

    def get_trial_balance_bs(
        self,
        fiscal_year: int,
        company_id: Optional[int] = None,
        start_month: Optional[int] = None,
        end_month: Optional[int] = None,
    ) -> Dict:
        """
        試算表（貸借対照表：BS）を取得

        Args:
            fiscal_year: 会計年度
            company_id: 事業所ID（省略時はデフォルト）
            start_month: 開始会計月（1-12）、省略時は期首
            end_month: 終了会計月（1-12）、省略時は期末

        Returns:
            {
                "trial_bs": {
                    "company_id": 1,
                    "fiscal_year": 2024,
                    "start_month": 1,
                    "end_month": 12,
                    "balances": [...],
                    ...
                }
            }
        """
        cid = company_id or self.company_id
        params = {
            "company_id": cid,
            "fiscal_year": fiscal_year,
        }
        if start_month is not None:
            params["start_month"] = start_month
        if end_month is not None:
            params["end_month"] = end_month

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        resp = self._request_with_retry("GET", f"/api/1/reports/trial_bs?{query_string}")
        return resp.json()

    def get_trial_balance_pl(
        self,
        fiscal_year: int,
        company_id: Optional[int] = None,
        start_month: Optional[int] = None,
        end_month: Optional[int] = None,
    ) -> Dict:
        """
        試算表（損益計算書：PL）を取得

        Args:
            fiscal_year: 会計年度
            company_id: 事業所ID（省略時はデフォルト）
            start_month: 開始会計月（1-12）、省略時は期首
            end_month: 終了会計月（1-12）、省略時は期末

        Returns:
            {
                "trial_pl": {
                    "company_id": 1,
                    "fiscal_year": 2024,
                    "start_month": 1,
                    "end_month": 12,
                    "balances": [...],
                    ...
                }
            }
        """
        cid = company_id or self.company_id
        params = {
            "company_id": cid,
            "fiscal_year": fiscal_year,
        }
        if start_month is not None:
            params["start_month"] = start_month
        if end_month is not None:
            params["end_month"] = end_month

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        resp = self._request_with_retry("GET", f"/api/1/reports/trial_pl?{query_string}")
        return resp.json()
