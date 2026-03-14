import yfinance as yf
from .base_skill import BaseSkill
from typing import Dict, Any

class MacroMonitorSkill(BaseSkill):
    """
    步驟 0：系統性風險監控 (Macro Hedge)
    監控匯率 (JPY, CNH, TWD)、利率 (JGB, US10Y)、大宗商品 (Oil, Gold, Copper) 與科技連動指標。
    """
    def __init__(self):
        super().__init__("MacroMonitor")
        # 定義監控門檻
        self.thresholds = {
            "USDJPY": 150.0,
            "WTI_OIL": 90.0,
            "VIX": 25.0,
            "USDTWD": 32.5,
            "US10Y": 4.5,
            "USDCNH": 7.3  # 人民幣警戒線
        }

    def analyze(self, symbol: str = "Global", **kwargs) -> Dict[str, Any]:
        """
        抓取宏觀數據並判斷風險狀態。
        """
        results = {
            "status": "安全",
            "triggers": [],
            "data": {}
        }

        # 定義抓取清單
        tickers = {
            # 匯率
            "USDJPY": "USDJPY=X",
            "USDTWD": "TWD=X",
            "USDCNH": "USDCNH=X",
            # 商品
            "WTI_OIL": "CL=F",
            "BRENT_OIL": "BZ=F",
            "GOLD": "GC=F",
            "COPPER": "HG=F",
            # 利率與情緒
            "VIX": "^VIX",
            "US10Y": "^TNX",
            # 科技連動
            "SOX": "^SOX",
            "TSM_ADR": "TSM",
            "NVDA": "NVDA"
        }

        for key, ticker in tickers.items():
            try:
                # 使用 fast_info 提高抓取速度
                val = yf.Ticker(ticker).fast_info['last_price']
                results["data"][key] = round(val, 2)
                
                # 門檻檢查
                if key in self.thresholds and val >= self.thresholds[key]:
                    results["triggers"].append(f"{key} ({val:.2f})")
            except Exception:
                results["data"][key] = "抓取失敗"

        # 嘗試抓取日債 10Y
        try:
            jgb = yf.Ticker("^JGB10Y").fast_info.get('last_price')
            if jgb:
                results["data"]["JGB_10Y"] = round(jgb, 3)
                if jgb >= 2.0:
                    results["triggers"].append(f"JGB_10Y ({jgb:.3f}%)")
            else:
                results["data"]["JGB_10Y"] = "N/A"
        except Exception:
            results["data"]["JGB_10Y"] = "N/A"

        # 判斷最終狀態
        if results["triggers"]:
            results["status"] = "警報 (建議保留 60% 以上現金)"
        
        return results

    def get_report(self, results: Dict[str, Any]) -> str:
        """
        將結果轉換為文字報告格式。
        """
        d = results["data"]
        report = [
            "### 系統性風險監控報告 (步驟 0)",
            f"- **狀態**: {results['status']}",
            f"- **匯率**: 日圓 {d.get('USDJPY', 'N/A')} / 台幣 {d.get('USDTWD', 'N/A')} / 離岸人民幣 {d.get('USDCNH', 'N/A')}",
            f"- **大宗商品**: 原油(WTI) {d.get('WTI_OIL', 'N/A')} / 布蘭特 {d.get('BRENT_OIL', 'N/A')} / 黃金 {d.get('GOLD', 'N/A')} / 銅 {d.get('COPPER', 'N/A')}",
            f"- **利率與科技**: 美債10Y {d.get('US10Y', 'N/A')}% / 日債10Y {d.get('JGB_10Y', 'N/A')}% / 費半 {d.get('SOX', 'N/A')} / NVDA {d.get('NVDA', 'N/A')}",
            f"- **市場情緒**: VIX 恐慌指數 {d.get('VIX', 'N/A')}"
        ]
        
        if results["triggers"]:
            report.append(f"\n**觸發警報項目**: {', '.join(results['triggers'])}")
        
        return "\n".join(report)
