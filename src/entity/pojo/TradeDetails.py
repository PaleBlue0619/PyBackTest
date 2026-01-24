import os
import pandas as pd
from typing import Dict, List

class TradeDetails:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 防止重复初始化
        if not TradeDetails._initialized:
            TradeDetails._initialized = True
            # 用户自定义成员变量
            self.stockRecord: Dict[int, Dict] = {}  # 股票成交记录
            self.futureRecord: Dict[int, Dict] = {} # 期货成交记录

    @classmethod
    def get_instance(cls) -> 'TradeDetails':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance