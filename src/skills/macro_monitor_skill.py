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
            "US10Y": 4.50,
            "USDCNH": 7.30,  # 人民幣警戒線
            "TSM_ADR_PREMIUM": 15.0,  # ADR 溢價過高警報
            "YIELD_SPREAD": 2.00  # 利差過大警報
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
            "NVDA": "NVDA",
            # 台積電現貨與大盤
            "TSMC_SPOT": "2330.TW",
            "TAIEX": "^TWII"
        }

        for key, ticker in tickers.items():
            try:
                # 使用 fast_info 提高抓取速度
                val = yf.Ticker(ticker).fast_info['last_price']
                results["data"][key] = round(val, 2)
                
                # 門檻檢查 (如果是一般數值且在 thresholds 中)
                if key in self.thresholds and val >= self.thresholds[key]:
                    results["triggers"].append(f"{key} ({val:.2f})")
            except Exception:
                results["data"][key] = "抓取失敗"

        # 1. 計算台積電 ADR 溢價率
        try:
            tsm = results["data"].get("TSM_ADR")
            tw = results["data"].get("TSMC_SPOT")
            twd = results["data"].get("USDTWD")
            
            if isinstance(tsm, (int, float)) and isinstance(tw, (int, float)) and isinstance(twd, (int, float)) and tw > 0:
                # 1股 TSM = 5股 2330.TW
                adr_tw_equiv = (tsm * 5) / twd
                premium = ((adr_tw_equiv - tw) / tw) * 100
                premium = round(premium, 2)
                results["data"]["TSM_ADR_PREMIUM"] = premium
                
                if premium >= self.thresholds["TSM_ADR_PREMIUM"]:
                    results["triggers"].append(f"TSM_ADR_PREMIUM ({premium:.2f}%)")
            else:
                results["data"]["TSM_ADR_PREMIUM"] = "計算失敗"
        except Exception:
            results["data"]["TSM_ADR_PREMIUM"] = "計算失敗"

        # 2. 計算美債-台股估算殖利率利差
        try:
            us10y = results["data"].get("US10Y")
            if isinstance(us10y, (int, float)):
                # 台股大盤平均殖利率基準大約為 2.80%
                tw_yield = 2.80
                spread = us10y - tw_yield
                spread = round(spread, 2)
                results["data"]["TW_EST_YIELD"] = tw_yield
                results["data"]["YIELD_SPREAD"] = spread
                
                if spread >= self.thresholds["YIELD_SPREAD"]:
                    results["triggers"].append(f"YIELD_SPREAD ({spread:.2f}%)")
            else:
                results["data"]["YIELD_SPREAD"] = "N/A"
        except Exception:
            results["data"]["YIELD_SPREAD"] = "N/A"

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
            results["status"] = "警報 (建議保留 50% 以上現金)"
        
        return results

    def get_report(self, results: Dict[str, Any]) -> str:
        """
        將結果轉換為文字報告格式。
        """
        d = results["data"]
        
        # 格式化 ADR 溢價顯示
        premium_val = d.get('TSM_ADR_PREMIUM', 'N/A')
        premium_text = f"{premium_val}%" if isinstance(premium_val, (int, float)) else premium_val
        
        # 格式化利差顯示
        spread_val = d.get('YIELD_SPREAD', 'N/A')
        spread_text = f"{spread_val}% (美債 {d.get('US10Y', 'N/A')}% - 台股估計 {d.get('TW_EST_YIELD', 'N/A')}%)" if isinstance(spread_val, (int, float)) else spread_val

        report = [
            "### 系統性風險監控報告 (步驟 0)",
            f"- **系統狀態**: {results['status']}",
            f"- **匯率**: 日圓 {d.get('USDJPY', 'N/A')} / 台幣 {d.get('USDTWD', 'N/A')} / 離岸人民幣 {d.get('USDCNH', 'N/A')}",
            f"- **跨市場套利與利差**: ",
            f"  * **台積電 ADR 溢價率**: {premium_text} (ADR: {d.get('TSM_ADR', 'N/A')} / 現貨: {d.get('TSMC_SPOT', 'N/A')})",
            f"  * **美債-台股殖利率利差**: {spread_text}",
            f"- **大宗商品**: 原油(WTI) {d.get('WTI_OIL', 'N/A')} / 布蘭特 {d.get('BRENT_OIL', 'N/A')} / 黃金 {d.get('GOLD', 'N/A')} / 銅 {d.get('COPPER', 'N/A')}",
            f"- **利率與科技**: 美債10Y {d.get('US10Y', 'N/A')}% / 日債10Y {d.get('JGB_10Y', 'N/A')}% / 費半 {d.get('SOX', 'N/A')} / NVDA {d.get('NVDA', 'N/A')}",
            f"- **市場情緒**: VIX 恐慌指數 {d.get('VIX', 'N/A')}"
        ]
        
        if results["triggers"]:
            report.append(f"\n**觸發警報項目**: {', '.join(results['triggers'])}")
        
        return "\n".join(report)
