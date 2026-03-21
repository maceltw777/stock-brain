from .base_skill import BaseSkill
from typing import Dict, Any

class InstitutionalSkill(BaseSkill):
    """
    籌碼面分析技能：負責獲取三大法人買賣超與融資融券數據。
    """
    def __init__(self):
        super().__init__("Institutional")

    def analyze(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """
        目前以生成精準搜尋指令為主，配合 Google Search 獲取最新籌碼數據。
        """
        # 建立針對籌碼面的搜尋關鍵字
        queries = [
            f"{symbol} 1000張大戶持股比例 變化 趨勢",
            f"{symbol} 三大法人 買賣超 近 5 日",
            f"{symbol} 外資 投信 自營商 買賣趨勢",
            f"{symbol} 融資融券 餘額變化 散戶動向"
        ]

        return {
            "symbol": symbol,
            "queries": queries,
            "instruction": "請搜尋上述關鍵字，特別關注『1000張大戶持股比例』近 3 週是否增加。同時彙整近 5 日三大法人的買賣超張數與融資融券趨勢，並評估籌碼是否集中。"
        }

    def get_report(self, search_results: str) -> str:
        return f"### 籌碼面分析報告 (步驟 3)\n{search_results}"
