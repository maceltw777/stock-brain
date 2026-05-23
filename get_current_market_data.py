import sys
import os
sys.path.append(os.getcwd())
from src.skills.macro_monitor_skill import MacroMonitorSkill
from src.skills.price_analysis_skill import PriceAnalysisSkill
from src.skills.institutional_skill import InstitutionalSkill
from src.skills.report_analyzer_skill import ReportAnalyzerSkill

def get_data():
    macro = MacroMonitorSkill()
    price = PriceAnalysisSkill()
    inst = InstitutionalSkill()
    report_analyzer = ReportAnalyzerSkill()
    
    print("--- Macro Data ---")
    macro_results = macro.analyze()
    print(macro.get_report(macro_results))
    
    print("\n--- TSEC (^TWII) Technical Data ---")
    twii_results = price.analyze("^TWII")
    print(price.get_report(twii_results))
    
    print("\n--- TSMC (2330.TW) Technical Data ---")
    tsmc_results = price.analyze("2330.TW")
    print(price.get_report(tsmc_results))
    
    print("\n--- Institutional & Derivatives Data ---")
    inst_results = inst.analyze("2330")
    print(inst.get_report(inst_results))
    
    print("\n--- Local RAG Knowledge Base ---")
    _, loaded_reports = report_analyzer.analyze()
    print(report_analyzer.get_report(loaded_reports))

if __name__ == "__main__":
    get_data()
