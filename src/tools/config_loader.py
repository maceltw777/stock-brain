import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# 載入 .env 環境變數
load_dotenv()

class ConfigLoader:
    def __init__(self, config_dir: str = "src/config", prompt_dir: str = "src/prompts"):
        self.config_path = Path(config_dir)
        self.prompt_path = Path(prompt_dir)
        self.settings = self._load_yaml("settings.yaml")
        self.prompts = self._load_yaml("prompts.yaml")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.rapid_api_key = os.getenv("RAPID_API_KEY")
        self.rapid_api_host = os.getenv("RAPID_API_HOST", "yfinance-stock-market-data.p.rapidapi.com")

    def _load_yaml(self, file_name: str) -> dict:
        file_path = self.config_path / file_name
        if not file_path.exists():
            print(f"警告：找不到設定檔 {file_path}")
            return {}
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get_long_prompt(self, file_name: str) -> str:
        """讀取 src/prompts/ 下的 Markdown 檔案作為長篇指令。"""
        file_path = self.prompt_path / f"{file_name}.md"
        if not file_path.exists():
            print(f"警告：找不到長篇指令檔 {file_path}")
            return ""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()


    def get_gemini_config(self) -> dict:
        config = self.settings.get("gemini", {})
        config["api_key"] = self.gemini_api_key
        return config

    def get_prompt(self, agent_name: str, key: str) -> str:
        return self.prompts.get(agent_name, {}).get(key, "")

# 全域設定實體
config = ConfigLoader()
