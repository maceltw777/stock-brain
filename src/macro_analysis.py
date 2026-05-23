import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from google import genai
from google.genai import types
from src.tools.config_loader import config
from src.skills.macro_monitor_skill import MacroMonitorSkill

def run_macro_analysis():
    # Load configuration
    gemini_config = config.get_gemini_config()
    api_key = (gemini_config.get("api_key") or "").strip()
    model_name = gemini_config.get("model_name", "gemini-2.0-flash")
    client = genai.Client(api_key=api_key)

    print("="*50)
    print("🚀 啟動國際大宗物價與原油價格分析")
    print("="*50)

    # 1. Fetch macro data using existing skill
    macro_skill = MacroMonitorSkill()
    print("正在抓取即時數據...")
    macro_results = macro_skill.analyze()
    macro_report = macro_skill.get_report(macro_results)
    
    print("\n" + macro_report)

    # 2. Prepare AI analysis prompt
    prompt = f"""
你是一位資深的全球總體經濟與大宗商品策略師。
請根據以下提供的即時市場數據，針對「國際大宗物價」與「石油價格」進行深度局勢分析。

### 即時市場數據 (Yahoo Finance):
{macro_report}

### 分析要求：
1. **能源市場分析**：針對 WTI 與 Brent 原油價格，分析目前的供需態勢、地緣政治影響或經濟預期。
2. **貴金屬與工業金屬**：分析黃金 (GOLD) 與 銅 (COPPER) 的走勢所反映的市場情緒（避險 vs. 成長預期）。
3. **宏觀環境聯動**：結合美元/日圓 (USDJPY)、美債 10 年期收益率 (US10Y) 以及 費城半導體 (SOX) 的數據，分析其對大宗商品價格的傳導效應。
4. **當前局勢判斷**：總結目前的全球經濟局勢（例如：通膨壓力、衰退風險、或復甦跡象），並給出投資建議（特別是針對台灣投資者的宏觀風險提醒）。

請使用專業、客觀且具備前瞻性的口吻進行分析。
"""

    print("\n正在進行 AI 綜合分析...")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="你是一位專業的全球宏觀分析師，擅長從多維度數據中提取趨勢。",
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        print("\n" + "="*20 + " 深度局勢分析報告 " + "="*20)
        print(response.text)
        print("="*50)
    except Exception as e:
        print(f"❌ AI 分析失敗: {str(e)}")

if __name__ == "__main__":
    run_macro_analysis()
