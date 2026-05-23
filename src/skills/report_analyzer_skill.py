import os
import datetime
from .base_skill import BaseSkill
from typing import Dict, Any, List, Tuple
from google.genai import types

class ReportAnalyzerSkill(BaseSkill):
    """
    步驟 1.5：本地報告分析與知識庫 (RAG)
    負責掃描 data/reports 目錄中的機構報告（PDF, TXT, MD），
    並利用 Gemini 原生多模態能力直接讀取與分析。
    """
    def __init__(self, reports_dir: str = "data/reports"):
        super().__init__("ReportAnalyzer")
        self.reports_dir = reports_dir
        self.max_files = 2  # 預設限制最多載入 2 份最新報告，防止 Token 過大

    def analyze(self, **kwargs) -> Tuple[List[Any], List[Dict[str, Any]]]:
        """
        掃描目錄，提取最新報告，並轉換為 Gemini 可直接理解的 Part 格式。
        """
        parts = []
        loaded_reports = []

        if not os.path.exists(self.reports_dir):
            return parts, loaded_reports

        # 1. 搜集所有支援的檔案
        allowed_extensions = {".pdf", ".txt", ".md"}
        files_with_mtime = []
        
        for root, _, files in os.walk(self.reports_dir):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in allowed_extensions:
                    full_path = os.path.join(root, file)
                    try:
                        mtime = os.path.getmtime(full_path)
                        files_with_mtime.append((full_path, file, ext, mtime))
                    except Exception:
                        pass

        # 2. 按修改時間排序（最新優先）
        files_with_mtime.sort(key=lambda x: x[3], reverse=True)
        selected_files = files_with_mtime[:self.max_files]

        # 3. 讀取並打包檔案
        for full_path, file_name, ext, mtime in selected_files:
            try:
                mod_time = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                size_kb = round(os.path.getsize(full_path) / 1024, 1)

                if ext == ".pdf":
                    # 使用二進位讀取並以 Part.from_bytes 封裝
                    with open(full_path, "rb") as f:
                        pdf_data = f.read()
                    
                    part = types.Part.from_bytes(
                        data=pdf_data,
                        mime_type="application/pdf"
                    )
                    parts.append(part)
                    loaded_reports.append({
                        "name": file_name,
                        "type": "PDF",
                        "size": f"{size_kb} KB",
                        "date": mod_time
                    })

                elif ext in {".txt", ".md"}:
                    # 純文字檔案直接讀取並包裝為 Part
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        text_data = f.read()
                    
                    part = types.Part.from_bytes(
                        data=text_data.encode("utf-8"),
                        mime_type="text/plain"
                    )
                    parts.append(part)
                    loaded_reports.append({
                        "name": file_name,
                        "type": "Text",
                        "size": f"{size_kb} KB",
                        "date": mod_time
                    })
            except Exception as e:
                print(f"⚠️ 讀取檔案 {file_name} 失敗: {str(e)}")

        return parts, loaded_reports

    def get_report(self, loaded_reports: List[Dict[str, Any]]) -> str:
        """
        格式化輸出已加載的報告清單。
        """
        if not loaded_reports:
            return "### 本地機構報告資料庫 (RAG)\n*目前 data/reports/ 資料夾中無已加載的報告。*"

        report = ["### 本地機構報告資料庫 (RAG)"]
        report.append(f"已成功載入最新 **{len(loaded_reports)}** 份機構報告進行深度交叉研判：")
        
        for idx, r in enumerate(loaded_reports, 1):
            report.append(f"{idx}. **[{r['type']}]** {r['name']} ({r['size']}) - 報告存檔時間: {r['date']}")
        
        return "\n".join(report)
