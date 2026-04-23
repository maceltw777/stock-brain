import sys
import os
sys.path.append(os.getcwd())
from src.skills.macro_monitor_skill import MacroMonitorSkill
from src.skills.price_analysis_skill import PriceAnalysisSkill

def get_data():
    macro = MacroMonitorSkill()
    price = PriceAnalysisSkill()
    
    print("--- Macro Data ---")
    macro_results = macro.analyze()
    print(macro.get_report(macro_results))
    
    print("\n--- TSEC (^TWII) Technical Data ---")
    twii_results = price.analyze("^TWII")
    print(price.get_report(twii_results))
    
    print("\n--- TSMC (2330.TW) Technical Data ---")
    tsmc_results = price.analyze("2330.TW")
    print(price.get_report(tsmc_results))

if __name__ == "__main__":
    get_data()
