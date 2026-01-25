import os, json, json5
import time
from typing import Callable,Dict,List
import src.entity.BackTester
from src.entity.pojo.Position import StockPosition,FuturePosition
from src.entity.pojo.Summary import StockSummary,FutureSummary
from src.entity.Context import Context
from src.entity.BackTester import BackTester
import dolphindb as ddb
import pandas as pd
import numpy as np

if __name__ == "__main__":
    # # 查看是否触发止盈止损
    symbol = "000877.SZ"
    static_profit = 0.05
    static_loss = 0.03
    dynamic_profit = 0.05
    dynamic_loss = 0.03
    df = pd.read_parquet(r"D:\BackTest\PyBackTest\data\stock_cn\bar")
    print(df[(df["TradeDate"]<=pd.Timestamp("20200131"))&(df["symbol"]==symbol)].reset_index(drop=True))
    # # 查看info信息
    # info = pd.read_parquet(r"D:\BackTest\PyBackTest\data\stock_cn\info")
    # print(info[info["symbol"]==symbol].reset_index(drop=True))