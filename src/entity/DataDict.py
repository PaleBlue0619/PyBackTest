import pandas as pd
from typing import Optional, TYPE_CHECKING

class DataDict:
    _instance = None
    _initialized = False
    _order_num = 0
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 防止重复初始化
        if not DataDict._initialized:
            DataDict._initialized = True
            # 行情数据
            self.stockKDict = {}  # 股票该日行情字典 TreeMap<LocalTime, Map<String, Bar>>
            self.futureKDict = {} # 期货该日行情字典
            self.optionKDict = {} # 期权该日行情字典

            # 信息数据
            self.stockInfoDict = {}     # 股票该日信息字典
            self.futureInfoDict = {}    # 期货该日信息字典
            self.optionInfoDict = {}    # 期权该日信息字典

    @classmethod
    def get_instance(cls) -> 'DataDict':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_stockKDict(self, k_dict: dict):
        self.stockKDict = k_dict

    def set_futureKDict(self, k_dict: dict):
        self.futureKDict = k_dict

    def set_optionKDict(self, k_dict: dict):
        self.optionKDict = k_dict

    def set_stockInfoDict(self, info_dict: dict):
        self.stockInfoDict = info_dict

    def set_futureInfoDict(self, info_dict: dict):
        self.futureInfoDict = info_dict

    def set_optionInfoDict(self, info_dict: dict):
        self.optionInfoDict = info_dict
