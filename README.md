# Taiwan Stock Analyst - Gemini CLI

這是一個基於 Agent 與 Skills 模式的台股分析工具。

## 架構說明

- **Agents (`src/agents/`)**: 負責決策。它會根據各項 Skills 的分析結果，透過 Gemini (LLM) 做出最終的判斷。
- **Skills (`src/skills/`)**: 負責具體的分析任務或資料獲取。例如：
    - `kd_skill.py`: 計算與分析 KD 指標。
    - `volume_skill.py`: 分析成交量變化。
    - `commodity_api_skill.py`: 呼叫 API 獲取大宗商品資訊。
- **Tools (`src/tools/`)**: 底層共用工具，例如股票資料抓取、資料庫連線等。

## 目錄結構

```text
/
├── src/
│   ├── agents/      # 決策 Agent
│   ├── skills/      # 分析技能 (KD, 交易量, API 等)
│   ├── tools/       # 共用工具 (API Client, 資料清洗)
│   ├── config/      # 設定檔
│   └── main.py      # 進入點
├── data/            # 歷史資料快取
├── tests/           # 測試程式
└── requirements.txt
```

## 未來擴充計畫

1. 實作 KD 值與成交量分析 Skill。
2. 串接大宗商品價格 API (如 Oil, Gold)。
3. 實作 Analyst Agent，匯整所有 Skill 報告並產出決策建議。
