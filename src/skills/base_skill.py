from abc import ABC, abstractmethod

class BaseSkill(ABC):
    """
    所有分析技能的基底類別。
    每項技能（如 KD, 成交量, API 呼叫）都需實作 analyze 方法。
    """
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def analyze(self, symbol: str, **kwargs):
        """
        執行具體的分析邏輯，並回傳分析報告（可以是字串或字典）。
        """
        pass
