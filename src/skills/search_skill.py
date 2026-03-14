from .base_skill import BaseSkill
from typing import Dict, Any, List

class SearchSkill(BaseSkill):
    """
    步驟 1：獲取關鍵資訊 (Search Skill)
    負責搜尋標的最新法說會、財報、券商報告及產業新聞。
    """
    def __init__(self):
        super().__init__("Search")

    def analyze(self, symbol: str, stock_name: str = "", **kwargs) -> Dict[str, Any]:
        """
        定義需要搜尋的關鍵字組合。
        具體的搜尋執行將交由整合了 Google Search 具能的 Agent 處理。
        """
        # 建立針對台股特性的搜尋關鍵字
        queries = [
            f"{symbol} {stock_name} 過去 12 小時內 關鍵新聞 影響 股市",
            f"台股 全市場 融資維持率 融資餘額 警報 斷頭 走勢",
            f"{symbol} {stock_name} 最新法說會 摘要 展望",
            f"{symbol} {stock_name} 產業新聞 趨勢 2024 2025",
            f"{symbol} {stock_name} 券商報告 目標價 評等"
        ]

        instruction = (
            "請使用 Google 搜尋執行上述關鍵字。特別注意：\n"
            "1. 必須搜尋並彙整過去 12 小時內可能影響股市的最新動態、新聞或事件。\n"
            "2. 判斷台股全市場的『融資維持率』是否低於 160%，是否有融資追繳斷頭風險。\n"
            "3. 針對標的資訊，彙整重點，特別關注『營收、毛利、庫存與展望』。"
        )

        return {
            "symbol": symbol,
            "stock_name": stock_name,
            "queries": queries,
            "instruction": instruction
        }

    def get_report(self, search_results: str) -> str:
        """
        將搜尋後的彙整內容格式化為報告。
        """
        return f"### 關鍵資訊搜尋結果 (步驟 1)\n{search_results}"
