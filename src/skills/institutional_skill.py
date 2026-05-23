import requests
import datetime
import re
from .base_skill import BaseSkill
from typing import Dict, Any

class InstitutionalSkill(BaseSkill):
    """
    籌碼面分析技能：負責獲取三大法人買賣超與融資融券數據。
    現在實作了真實爬蟲數據獲取與雙重 Fallback 備用機制。
    """
    def __init__(self):
        super().__init__("Institutional")

    def _fetch_twse_margin(self) -> Dict[str, Any]:
        """抓取大盤融資餘額，從今天開始往回嘗試 7 天直到抓到有數據的交易日"""
        today = datetime.date.today()
        for i in range(7):
            query_date = today - datetime.timedelta(days=i)
            date_str = query_date.strftime("%Y%m%d")
            url = f"https://www.twse.com.tw/exchangeReport/MI_MARGN?response=json&selectType=MS&date={date_str}"
            try:
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("stat") == "OK" and "data" in data:
                        for row in data["data"]:
                            # 項目欄位為 row[0]
                            if "融資" in row[0] and "元" in row[0]:
                                val_str = row[5].replace(",", "")
                                val = float(val_str)
                                # 換算為億元
                                if val > 10000000000: # 元計
                                    margin_value_billion = round(val / 100000000, 2)
                                else: # 千元計
                                    margin_value_billion = round(val / 100000, 2)
                                return {
                                    "success": True,
                                    "margin_debt_billion": margin_value_billion,
                                    "date": date_str
                                }
            except Exception:
                pass
        return {"success": False, "error": "無法取得近期大盤融資餘額"}

    def _fetch_taifex_futures(self) -> Dict[str, Any]:
        """抓取外資台指期未平倉多空淨額口數"""
        url = "https://www.taifex.com.tw/cht/3/callsDetail"
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                html_content = resp.text
                # 用 Regex 先找到 "臺股期貨" 這個大表格的起點
                tx_match = re.search(r"臺股期貨.*?外資及陸資", html_content, re.DOTALL)
                if tx_match:
                    # 從 "外資及陸資" 開始截取後面的表格內容
                    start_idx = html_content.find("外資及陸資", tx_match.start())
                    sub_html = html_content[start_idx:start_idx+3000]
                    # 提取所有在 <td> 裡面的數字
                    td_vals = re.findall(r'<td[^>]*>\s*([-\d,]+)\s*</td>', sub_html)
                    # 清洗數字：移除逗號
                    clean_vals = []
                    for v in td_vals:
                        v_clean = v.replace(",", "").strip()
                        if re.match(r'^-?\d+$', v_clean):
                            clean_vals.append(int(v_clean))
                    
                    # 根據期交所台指期外資的行結構：
                    # 多方交易(口數/契約金額)、空方交易(口數/契約金額)、多空淨額(口數/契約金額)
                    # 多方未平倉(口數/契約金額)、空方未平倉(口數/契約金額)、多空淨額未平倉(口數/契約金額)
                    # 多空淨額未平倉口數通常在第 11 個整數值 (index 10)
                    if len(clean_vals) >= 11:
                        net_outstanding = clean_vals[10]
                        return {
                            "success": True,
                            "futures_net_position": net_outstanding
                        }
        except Exception as e:
            return {"success": False, "error": str(e)}
        return {"success": False, "error": "網頁結構解析失敗"}

    def analyze(self, symbol: str, **kwargs) -> Dict[str, Any]:
        # 1. 執行實體抓取
        margin_res = self._fetch_twse_margin()
        futures_res = self._fetch_taifex_futures()

        # 2. 建立基本結果字典
        results = {
            "symbol": symbol,
            "data_fetched": False,
            "margin_debt_billion": None,
            "margin_date": None,
            "futures_net_position": None,
            "queries": [
                f"{symbol} 1000張大戶持股比例 變化 趨勢",
                f"{symbol} 三大法人 買賣超 近 5 日",
                f"{symbol} 外資 投信 自營商 買賣趨勢",
                f"{symbol} 融資融券 餘額變化 散戶動向"
            ],
            "instruction": "請搜尋上述關鍵字，特別關注『1000張大戶持股比例』近 3 週是否增加。同時彙整近 5 日三大法人的買賣超張數與融資融券趨勢，並評估籌碼是否集中。"
        }

        # 3. 填入數據 (如果有抓到)
        if margin_res.get("success"):
            results["margin_debt_billion"] = margin_res["margin_debt_billion"]
            results["margin_date"] = margin_res["date"]
            results["data_fetched"] = True
            
        if futures_res.get("success"):
            results["futures_net_position"] = futures_res["futures_net_position"]
            results["data_fetched"] = True

        return results

    def get_report(self, results: Dict[str, Any]) -> str:
        report = ["### 籌碼面分析報告 (步驟 3)"]
        
        if results.get("data_fetched"):
            report.append("**【大盤即時籌碼指標】**")
            margin = results.get("margin_debt_billion")
            margin_date = results.get("margin_date")
            margin_text = f"{margin} 億元 (統計日期: {margin_date})" if margin else "抓取失敗"
            report.append(f"- **大盤融資餘額**: {margin_text}")
            
            futures = results.get("futures_net_position")
            if futures is not None:
                futures_type = "淨多單" if futures >= 0 else "淨空單"
                report.append(f"- **外資期指未平倉**: {futures_type} {abs(futures):,} 口")
            else:
                report.append("- **外資期指未平倉**: 抓取失敗")
            
            report.append("\n**【AI 深度研判建議與額外搜尋任務】**")
        else:
            report.append("*⚠️ 即時籌碼數據直接抓取失敗，已啟動備用搜尋機制。*")

        report.append("請特別關注『1000張大戶持股比例』近 3 週是否增加。同時彙整近 5 日三大法人的買賣超張數與融資融券趨勢，並評估籌碼是否集中。")
        return "\n".join(report)
