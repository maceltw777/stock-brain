import argparse
import sys
from src.agents.analyst_agent import AnalystAgent
from src.tools.config_loader import config

def main():
    parser = argparse.ArgumentParser(description="台股投資助理 - 基於 Gemini & 股立核心邏輯")
    parser.add_argument("--stock", type=str, help="股票代號 (例如: 2330)")
    parser.add_argument("--name", type=str, default="", help="股票名稱 (選擇性，例如: 台積電)")
    
    args = parser.parse_args()

    if not args.stock:
        default_stocks = config.settings.get("default_stocks", [])
        print("請指定股票代號。例如: python src/main.py --stock 2330")
        if default_stocks:
            print(f"預設追蹤清單: {', '.join(default_stocks)}")
        sys.exit(1)

    symbol = args.stock
    name = args.name

    print("="*50)
    print(f"🚀 啟動台股分析助理 - 標的: {symbol} {name}")
    print("="*50)

    try:
        agent = AnalystAgent()
        report = agent.run_analysis(symbol, name)

        print("\n" + "="*20 + " 最終分析報告 " + "="*20)
        print(report)
        print("="*50)

    except Exception as e:
        error_msg = str(e)
        # 捕捉 API 額度耗盡、網路錯誤或 API Key 缺失
        if any(keyword in error_msg for keyword in ["RESOURCE_EXHAUSTED", "429", "API key", "API_KEY"]):
            print(f"\n⚠️ Gemini API 無法使用 ({error_msg})，改為顯示原始數據報告：")
            
            # 直接使用已經初始化過的 agent (如果有的話) 或重新建立一個
            try:
                fallback_agent = AnalystAgent()
                macro_results = fallback_agent.macro_skill.analyze()
                price_results = fallback_agent.price_skill.analyze(symbol)
                
                print("\n" + "="*20 + " 原始數據報告 (無 AI 介入) " + "="*20)
                print(fallback_agent.macro_skill.get_report(macro_results))
                print("\n")
                print(fallback_agent.price_skill.get_report(price_results))
                print("\n[提示] 以上為即時抓取數據。待 API 額度恢復後可產出三層訓練法深度分析。")
            except Exception as inner_e:
                print(f"❌ 無法產出 fallback 報告: {str(inner_e)}")
            
            print("="*50)
        else:
            print(f"❌ 執行分析時發生錯誤: {error_msg}")
            sys.exit(1)

if __name__ == "__main__":
    main()
