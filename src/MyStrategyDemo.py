import os, json, json5
from typing import Callable,Dict,List
import src.entity.BackTester
from src.entity.Counter import Counter
from src.entity.Context import Context
from src.entity.BackTester import BackTester
import dolphindb as ddb
import pandas as pd

def initialize(context: Dict):
    """
    策略回调初始化函数
    """
    print("Backtest Start!")
    print("Initialize context", context)

def beforeTrading(self: Counter, context: Context):
    """
    盘前回调函数
    """
    # 获取框架维护的基本属性 -> 时间
    currentDate = context.current_date
    print("Current BackTest DayTime is", currentDate)

def afterTrading(self: Counter, context: Context):
    """
    盘后回调函数
    """
    # 获取框架维护的基本属性 -> 时间
    currentDate = context.current_date
    print("Current Backtest DayTime is", currentDate)

def onTrade(self: Counter, context: Context, trade: Dict[str, any]):
    """
    成交回报函数
    trade: {"timestamp":, "symbol":, "price":, "direction": }
    """
    print("OnTrade", trade["timestamp"], trade["symbol"], trade["price"], trade["direction"])


def onBar(self: Counter, context: Context, msg: Dict[str, Dict[str, float]]):
    """
    Bar回调函数
    msg: {"标的1":{"open": "high": ...}}
    """
    # 获取框架维护的基本属性 -> 时间
    currentDate = context.current_date
    currentTimestamp = context.current_timestamp

    # 进行下单操作
    self.orderCloseStock("long", "000001.XSHE", 1000, 10.0,
                            min_order_timestamp=currentTimestamp,
                            max_order_timestamp=pd.Timestamp("20200105"),
                            partial_order=False, reason="testClose")

def finalize(context: Context):
    """
    策略回调结束函数
    """
    print("Backtest Finalize!")

if __name__ == "__main__":
    # 获取配置文件
    config = {
        "context": {"param": 1.0},
        "start_date": "20200101",
        "end_date": "20210101",
        "run_stock": True,
        "run_future": True,
        "freq": 2, # 1(分钟频) # 2(日频)
        "cash": 200000,
        "stockCash": 100000,
        "futureCash": 100000,
        "stockBarPath": r"D:\BackTest\PyBackTest\data\stock_cn\bar",
        "stockInfoPath": r"D:\BackTest\PyBackTest\data\stock_cn\info",
        "futureBarPath": r"D:\BackTest\PyBackTest\data\future_cn\bar",
        "futureInfoPath": r"D:\BackTest\PyBackTest\data\future_cn\info",
    }
    # 构造回调函数字典
    eventCallBacksDict = {
        "initialize": initialize,
        "beforeTrading": beforeTrading,
        "afterTrading": afterTrading,
        "onTrade": onTrade,
        "onBar": onBar,
        "finalize": finalize
    }
    # 创建回测实例
    BackTester = BackTester("MyStrategyDemo", config, eventCallBacksDict,
                            session=ddb.session("localhost",8848, "admin", "123456"))
    BackTester.append(
        "stock",
        pd.read_parquet(r"D:\BackTest\PyBackTest\data\stock_cn\bar\20200102.pqt"),
        pd.read_parquet(r"D:\BackTest\PyBackTest\data\stock_cn\info\20200102.pqt")
    )
    print(BackTester.dataDict.stockInfoDict)


