import os
import pandas as pd
from typing import Dict, List
from src.entity.Context import Context

class Statistics:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 防止重复初始化
        if not Statistics._initialized:
            Statistics._initialized = True
            # 用户自定义类
            self.cashDict: Dict[pd.Timestamp, float] = {}
            self.stockCashDict: Dict[pd.Timestamp, float] = {}
            self.futureCashDict: Dict[pd.Timestamp, float] = {}
            self.profitDict: Dict[pd.Timestamp, float] = {}
            self.realTimeProfitDict: Dict[pd.Timestamp, float] = {}
            self.stockProfitDict: Dict[pd.Timestamp, float] = {}
            self.stockRealTimeProfitDict: Dict[pd.Timestamp, float] = {}
            self.futureProfitDict: Dict[pd.Timestamp, float] = {}
            self.futureRealTimeProfitDict: Dict[pd.Timestamp, float] = {}

    @classmethod
    def get_instance(cls) -> 'Statistics':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def update_from_context(self, context: Context):
        """从Context中-> 填入当期的数值"""
        self.cashDict[context.current_date] = context.cash
        self.stockCashDict[context.current_date] = context.stockCash
        self.futureCashDict[context.current_date] = context.futureCash
        self.profitDict[context.current_date] = context.profit
        self.realTimeProfitDict[context.current_date] = context.realTimeProfit
        self.stockProfitDict[context.current_date] = context.stockProfit
        self.stockRealTimeProfitDict[context.current_date] = context.stockRealTimeProfit
        self.futureProfitDict[context.current_date] = context.futureProfit
        self.futureRealTimeProfitDict[context.current_date] = context.futureRealTimeProfit
