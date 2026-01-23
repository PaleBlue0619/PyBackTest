import os, json, json5
import time
from typing import Callable,Dict,List
import src.entity.BackTester
from src.entity.pojo.Position import StockPosition,FuturePosition
from src.entity.pojo.Summary import StockSummary,FutureSummary
from src.entity.Counter import Counter
from src.entity.Context import Context
from src.entity.BackTester import BackTester
import dolphindb as ddb
import pandas as pd
import numpy as np

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
    currentDate = context["TradeDate"]
    currentTime = context["TradeTime"]
    print("Current BackTest DayTime is", currentDate, currentTime)

def afterTrading(self: Counter, context: Context):
    """
    盘后回调函数
    """
    # 获取框架维护的基本属性 -> 时间
    currentDate = context["TradeDate"]
    currentTime = context["TradeTime"]
    print("Current Backtest DayTime is", currentDate, currentTime)

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
    currentDate = context["TradeDate"]
    currentTimestamp = context["TradeTime"]

    # 查看当前持仓视图(相对持仓数据传输成本更小, 回测速度更快) ->进行下单操作
    stockPos: Dict[str,StockSummary] = self.getStockSummary(direction="long",symbol=["000001.SZ"])
    futurePos: Dict[str,FutureSummary] = self.getFutureSummary(direction="long",symbol=["A2001.DCE"])
    if "000001.SZ" not in stockPos:
        self.orderOpenStock("long", "000001.SZ", 1000, 10.0,
                            static_profit=0.05,static_loss=0.05,
                            dynamic_profit=0.05,dynamic_loss=0.05,
                            commission=0.0,
                            min_timestamp=currentTimestamp, # 最小持仓时间 -> 小于最短时间无法平仓
                            max_timestamp=pd.Timestamp("20210101"), # 最大持仓时间 -> 超时自动平仓
                            min_order_timestamp=currentTimestamp,   # 最小下单时间
                            max_order_timestamp=pd.Timestamp("20210101"),   # 最大订单时间 -> 超时自动撤单
                            partial_order=False, reason="testOpenStock")
    if "A2001.DCE" not in futurePos:
        self.orderOpenFuture("long", "A2001.DCE", 1000, 10.0,
                             static_profit=0.05, static_loss=0.05,
                             dynamic_profit=0.05, dynamic_loss=0.05,
                             commission=0.0,
                             min_timestamp=currentTimestamp,    # 最小持仓时间 -> 小于最短时间无法平仓
                             max_timestamp=pd.Timestamp("20210101"),    # 最大持仓时间
                             min_order_timestamp=currentTimestamp,  # 最小下单时间
                             max_order_timestamp=pd.Timestamp("20210101"), # 最大订单时间 -> 超时自动撤单
                             partial_order=False, reason="testOpenFuture")

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
        "futureCash": 100000
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
    stockBar = pd.read_parquet(r"D:\BackTest\PyBackTest\data\stock_cn\bar")
    stockInfo = pd.read_parquet(r"D:\BackTest\PyBackTest\data\stock_cn\info")
    futureBar = pd.read_parquet(r"D:\BackTest\PyBackTest\data\future_cn\bar")
    futureInfo = pd.read_parquet(r"D:\BackTest\PyBackTest\data\future_cn\info")
    t0 = time.time()
    BackTester.append(
        stockBar=stockBar,
        stockInfo=stockInfo,
        futureBar=futureBar,
        futureInfo=futureInfo
    )
    # 新增缓存数据
    t1 = time.time()
    print(BackTester.UserContext)
    print(BackTester.SysContext.__dict__)
    print("耗时:", t1-t0, "s")

