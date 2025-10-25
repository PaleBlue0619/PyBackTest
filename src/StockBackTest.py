"""
完整的PyBackTest实现股票回测实例
"""
import json, json5
import pandas as pd
from src.entity.Counter import *

if __name__ == "__main__":
    startDate = "2020.01.01"
    endDate = "2021.01.01"
    barPath = r"D:\\BackTest\\JavaBackTest\\data\\stock_cn\\kbar"
    infoPath = r"D:\\BackTest\\JavaBackTest\\data\\stock_cn\\info"
    configPath = r"D:\\BackTest\\JavaBackTest\\src\\main\\java\\com\\maxim\\backtest_config.json"

    with open(configPath, "r") as f:
        config = json5.load(f)
    for tradeDate in [pd.Timestamp("20200102"),
                      pd.Timestamp("20200103"),
                      pd.Timestamp("20200106")]:
        


