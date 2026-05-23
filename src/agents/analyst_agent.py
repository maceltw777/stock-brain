from google import genai
from google.genai import types
from src.tools.config_loader import config
from src.skills.macro_monitor_skill import MacroMonitorSkill
from src.skills.search_skill import SearchSkill
from src.skills.price_analysis_skill import PriceAnalysisSkill
from src.skills.institutional_skill import InstitutionalSkill
from src.skills.report_analyzer_skill import ReportAnalyzerSkill

class AnalystAgent:
    """
    台股分析 Agent
    整合所有 Skills 與『股立邏輯核心』進行分析。
    """
    def __init__(self):
        # 載入設定
        gemini_config = config.get_gemini_config()
        api_key = (gemini_config.get("api_key") or "").strip()
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None
        
        # 讀取核心邏輯
        self.strategy_core = config.get_long_prompt("strategy_core")
        self.model_name = gemini_config.get("model_name", "gemini-2.0-flash")
        
        # 初始化 Skills
        self.macro_skill = MacroMonitorSkill()
        self.search_skill = SearchSkill()
        self.price_skill = PriceAnalysisSkill()
        self.inst_skill = InstitutionalSkill()
        self.report_analyzer_skill = ReportAnalyzerSkill()

    def run_analysis(self, symbol: str, stock_name: str = ""):
        """
        執行完整分析流程。
        """
        print(f"正在執行標的 {symbol} {stock_name} 的完整分析流程...")

        # 1. 抓取各項 Skill 數據
        macro_results = self.macro_skill.analyze()
        price_results = self.price_skill.analyze(symbol)
        search_info = self.search_skill.analyze(symbol, stock_name)
        inst_info = self.inst_skill.analyze(symbol)
        local_parts, loaded_reports = self.report_analyzer_skill.analyze()

        # 2. 數據完整性檢查 (Data Validation)
        is_data_sufficient, reason = self._validate_data_quality(macro_results, price_results)
        if not is_data_sufficient:
            print(f"⚠️ 數據不齊全，跳過 AI 綜合分析。原因: {reason}")
            inst_report = self.inst_skill.get_report(inst_info)
            local_report = self.report_analyzer_skill.get_report(loaded_reports)
            return f"{self.macro_skill.get_report(macro_results)}\n\n{self.price_skill.get_report(price_results)}\n\n{inst_report}\n\n{local_report}\n\n[提示] 數據缺失，暫不啟動 AI 研判。"

        # 3. 準備 AI 分析 Context
        macro_report = self.macro_skill.get_report(macro_results)
        price_report = self.price_skill.get_report(price_results)
        inst_report = self.inst_skill.get_report(inst_info)
        local_report = self.report_analyzer_skill.get_report(loaded_reports)
        
        # 擴充搜尋關鍵字：加入期貨、融資、官股等維度
        extended_queries = [
            "台指期 外資留倉口數 今日",
            "台股 Put/Call Ratio 最新走勢",
            "今日 融資餘額 增減 變動",
            "八大官股行庫 買賣超 今日",
            "台股 族群漲跌 分佈趨勢"
        ]
        all_queries = search_info['queries'] + inst_info['queries'] + extended_queries
        
        full_context = f"""
當前標的: {symbol} {stock_name}

{macro_report}

{price_report}

{inst_report}

{local_report}

請根據上述實時數據（特別注意日圓、台幣、WTI原油、NVDA、US10Y、VIX，以及最新計算出的 **台積電 ADR 溢價率**、**美債-台股利差**、**外資期指淨多/空單口數**、**大盤融資餘額** 之間的跨市場關聯），
並結合隨信附上的 **【本地機構報告資料庫】中最新的總體經濟/產業分析預測（如：美國/台灣經濟展望、降息機率、央行貨幣政策動向等）**，
並額外搜尋以下關鍵資訊（含過去 12 小時最新動態）後，依據『三層訓練法』進行深度分析：
關鍵字: {", ".join(all_queries)}

### 額外查核要求：
1. 期貨籌碼：目前抓取到的外資期指淨部位是否異常？與大盤創高是否出現背離？Put/Call Ratio 反映的情緒為何？
2. 洗盤狀態：目前抓取到的大盤融資餘額是否出現顯著的槓桿減肥？官股是否有護盤或高檔賣超跡象？
3. 結構問題：今日市場是權值股獨撐，還是有其他族群帶頭齊揚？

分析要求: {search_info['instruction']} 並且包含 {inst_info['instruction']}

### 矛盾偵測提醒 (Anomaly Detection)
若發現數據指標背離（如股價漲但量縮、宏觀風險警報但大盤創高、台積電 ADR 溢價率過高但現貨滯漲、外資在期貨留存歷史級別巨量空單但現貨同步大買等），請務必以 **【⚠️ 數據矛盾提醒】** 區塊標註並深入探討其避險意圖與籌碼陷阱。
"""

        # 4. 執行 AI 綜合研判
        if not self.client:
            raise Exception("No API key provided. AI analysis is disabled.")
            
        # 準備多模態內容
        contents = [full_context]
        if local_parts:
            contents.extend(local_parts)
            
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=self.strategy_core,
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        return response.text

    def _validate_data_quality(self, macro_results, price_results):
        """檢查數據是否足夠讓 AI 進行分析。"""
        if "error" in price_results or not price_results.get("current_price"):
            return False, "無法取得技術面股價數據"
        
        valid_macro_count = sum(1 for v in macro_results.get("data", {}).values() if v != "抓取失敗")
        if valid_macro_count == 0:
            return False, "無法取得任何宏觀風險數據"
            
        return True, "數據齊全"
