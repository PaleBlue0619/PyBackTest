import os
import pandas as pd
from typing import Dict, List

class OrderDetails:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 防止重复初始化
        if not OrderDetails._initialized:
            OrderDetails._initialized = True
            # 用户自定义类
            self.stockRecord: Dict[int, Dict] = {}  # 股票记录
            self.futureRecord: Dict[int, Dict] = {} # 期货记录

    @classmethod
    def get_instance(cls) -> 'OrderDetails':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance