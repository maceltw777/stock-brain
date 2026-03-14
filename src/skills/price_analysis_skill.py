import yfinance as yf
import pandas as pd
from .base_skill import BaseSkill
from typing import Dict, Any

class PriceAnalysisSkill(BaseSkill):
    """
    技術面分析技能：負責計算 KD、MA 與成交量分析。
    """
    def __init__(self):
        super().__init__("PriceAnalysis")

    def analyze(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """
        獲取歷史股價並計算技術指標。
        """
        # 台股在 yfinance 需要加上 .TW 或 .TWO
        ticker_symbol = f"{symbol}.TW"
        try:
            df = yf.download(ticker_symbol, period="6mo", interval="1d", progress=False)
            if df.empty:
                # 嘗試興櫃/上櫃代碼
                df = yf.download(f"{symbol}.TWO", period="6mo", interval="1d", progress=False)
            
            if df.empty:
                return {"error": f"找不到 {symbol} 的股價數據"}

            # 修正 yfinance 多重索引問題
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # 1. 計算移動平均線 (MA)
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['MA60'] = df['Close'].rolling(window=60).mean()

            # 2. 計算 KD 值 (9, 3, 3)
            low_min = df['Low'].rolling(window=9).min()
            high_max = df['High'].rolling(window=9).max()
            df['RSV'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
            
            df['K'] = 50.0
            df['D'] = 50.0
            for i in range(1, len(df)):
                if pd.notna(df['RSV'].iloc[i]):
                    df.loc[df.index[i], 'K'] = (2/3) * df['K'].iloc[i-1] + (1/3) * df['RSV'].iloc[i]
                    df.loc[df.index[i], 'D'] = (2/3) * df['D'].iloc[i-1] + (1/3) * df['K'].iloc[i]

            # 3. 取得最新數據
            latest = df.iloc[-1]
            prev = df.iloc[-2]

            return {
                "symbol": symbol,
                "current_price": round(float(latest['Close']), 2),
                "change_percent": round(float((latest['Close'] - prev['Close']) / prev['Close'] * 100), 2),
                "ma5": round(float(latest['MA5']), 2),
                "ma20": round(float(latest['MA20']), 2),
                "ma60": round(float(latest['MA60']), 2),
                "k": round(float(latest['K']), 2),
                "d": round(float(latest['D']), 2),
                "volume": int(latest['Volume']),
                "volume_ma5": int(df['Volume'].tail(5).mean()),
                "trend": "多頭" if latest['MA5'] > latest['MA20'] > latest['MA60'] else "空頭" if latest['MA5'] < latest['MA20'] < latest['MA60'] else "盤整"
            }
        except Exception as e:
            return {"error": str(e)}

    def get_report(self, results: Dict[str, Any]) -> str:
        if "error" in results:
            return f"### 技術面分析\n無法獲取數據: {results['error']}"
        
        return f"""### 技術面分析報告 (步驟 2)
- **當前股價**: {results['current_price']} ({results['change_percent']}%)
- **均線趨勢**: {results['trend']} (MA5: {results['ma5']}, MA20: {results['ma20']}, MA60: {results['ma60']})
- **KD 指標**: K={results['k']}, D={results['d']} ({'超買' if results['k'] > 80 else '超賣' if results['k'] < 20 else '常態'})
- **成交量**: {results['volume']:,} (5日均量: {results['volume_ma5']:,})
"""
