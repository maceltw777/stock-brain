import os
import datetime
import shutil
from .base_skill import BaseSkill
from typing import Dict, Any, List, Tuple
from google.genai import types

class ReportAnalyzerSkill(BaseSkill):
    """
    步驟 1.5：本地報告分析與自適應知識庫 (RAG)
    自動掃描 data/reports 目錄中的機構報告，
    並對超過 14 天的舊 PDF 進行自動歸檔與文字化優化，以節省 Token 消耗。
    """
    def __init__(self, reports_dir: str = "data/reports"):
        super().__init__("ReportAnalyzer")
        self.reports_dir = reports_dir
        self.archive_dir = os.path.join(reports_dir, "archive")
        self.max_files = 3  # 最大載入報告數
        self.aging_days = 14  # 超過 14 天的 PDF 將自動進行文字化歸檔

        # 自動建立目錄
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.archive_dir, exist_ok=True)

    def analyze(self, **kwargs) -> Tuple[List[Any], List[Dict[str, Any]], List[str]]:
        """
        掃描目錄，自動處理老化檔案，返回多模態 Parts、加載摘要以及需要生成摘要的舊檔案清單。
        """
        parts = []
        loaded_reports = []
        reports_needing_summary = []  # 存放超過 14 天且尚未建立摘要的舊 PDF 檔名

        if not os.path.exists(self.reports_dir):
            return parts, loaded_reports, reports_needing_summary

        now = datetime.datetime.now()
        files_with_mtime = []

        # 1. 搜集 reports 資料夾下的所有檔案 (不包含歸檔資料夾)
        for file in os.listdir(self.reports_dir):
            full_path = os.path.join(self.reports_dir, file)
            if os.path.isdir(full_path):
                continue  # 跳過 archive 等子目錄

            ext = os.path.splitext(file)[1].lower()
            if ext in {".pdf", ".txt", ".md"}:
                try:
                    mtime = os.path.getmtime(full_path)
                    files_with_mtime.append((full_path, file, ext, mtime))
                except Exception:
                    pass

        # 2. 自動執行老化檔案的歸檔與管理
        active_files = []
        for full_path, file_name, ext, mtime in files_with_mtime:
            file_age_days = (now - datetime.datetime.fromtimestamp(mtime)).days

            if ext == ".pdf" and file_age_days >= self.aging_days:
                # 這是超過 14 天的舊 PDF，檢查是否已有文字摘要檔
                base_name = os.path.splitext(file_name)[0]
                summary_name = f"{base_name}_summary.txt"
                summary_path = os.path.join(self.reports_dir, summary_name)

                if os.path.exists(summary_path):
                    # 【核心自動化】已有文字摘要，自動將沉重的 PDF 移至歸檔資料夾，減少 Token 負擔
                    try:
                        archive_path = os.path.join(self.archive_dir, file_name)
                        shutil.move(full_path, archive_path)
                        print(f"📦 [自動歸檔] 舊報告 {file_name} 已有文字摘要，已自動歸檔原 PDF 至 archive/ 目錄下。")
                    except Exception as e:
                        print(f"⚠️ [自動歸檔失敗] {file_name}: {str(e)}")
                else:
                    # 超過 14 天但尚未建立摘要，標記需要 AI 進行自動歸檔摘要任務
                    reports_needing_summary.append(file_name)
                    active_files.append((full_path, file_name, ext, mtime))
            else:
                # 活躍檔案 (新 PDF 或文字檔)
                active_files.append((full_path, file_name, ext, mtime))

        # 3. 按修改時間排序活躍檔案（最新優先）
        active_files.sort(key=lambda x: x[3], reverse=True)
        selected_files = active_files[:self.max_files]

        # 4. 讀取並打包檔案為 Part
        for full_path, file_name, ext, mtime in selected_files:
            try:
                mod_time = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                size_kb = round(os.path.getsize(full_path) / 1024, 1)

                if ext == ".pdf":
                    with open(full_path, "rb") as f:
                        pdf_data = f.read()
                    
                    part = types.Part.from_bytes(
                        data=pdf_data,
                        mime_type="application/pdf"
                    )
                    parts.append(part)
                    loaded_reports.append({
                        "name": file_name,
                        "type": "PDF(活躍)",
                        "size": f"{size_kb} KB",
                        "date": mod_time
                    })

                elif ext in {".txt", ".md"}:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        text_data = f.read()
                    
                    part = types.Part.from_bytes(
                        data=text_data.encode("utf-8"),
                        mime_type="text/plain"
                    )
                    parts.append(part)
                    
                    # 判斷是否為自動歸檔生成的摘要檔
                    rep_type = "歸檔摘要" if file_name.endswith("_summary.txt") else "文字報告"
                    loaded_reports.append({
                        "name": file_name,
                        "type": rep_type,
                        "size": f"{size_kb} KB",
                        "date": mod_time
                    })
            except Exception as e:
                print(f"⚠️ 讀取檔案 {file_name} 失敗: {str(e)}")

        return parts, loaded_reports, reports_needing_summary

    def get_report(self, loaded_reports: List[Dict[str, Any]]) -> str:
        if not loaded_reports:
            return "### 本地機構報告資料庫 (自適應 RAG)\n*目前無活躍的報告或已加載的歸檔摘要。*"

        report = ["### 本地機構報告資料庫 (自適應 RAG)"]
        report.append(f"已成功載入最新 **{len(loaded_reports)}** 份報告/歸檔摘要進行深度研判：")
        
        for idx, r in enumerate(loaded_reports, 1):
            report.append(f"{idx}. **[{r['type']}]** {r['name']} ({r['size']}) - 存檔時間: {r['date']}")
        
        return "\n".join(report)
