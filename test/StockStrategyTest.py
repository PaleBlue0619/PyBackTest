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

def initialize(self: BackTester, context: Dict):
    """
    策略回调初始化函数
    """
    print("Backtest Start!")
    print("Initialize context", context)
    # 调仓日期
    context["posDateList"] = [self.date_list[i] for i in range(0, len(self.date_list)) if i%5 == 0]

def beforeTrading(self: BackTester, context: Context):
    """
    每日盘前回调函数
    """
    # 获取框架维护的基本属性 -> 时间
    currentDate = context["TradeDate"]
    currentTime = context["TradeTime"]
    print("Current BackTest DayTime is", currentDate, currentTime)

def afterTrading(self: BackTester, context: Context):
    """
    每日盘后回调函数 -> 每日盘后根据今日因子生成下一个交易日的交易信号
    """
    # 获取框架维护的基本属性 -> 时间
    currentDate = context["TradeDate"]
    currentTime = context["TradeTime"]
    nextDate = context["NextDate"]
    # 清空当前标的 + 目标权重
    context["dayLongDict"] = {}
    context["dayShortDict"] = {}
    # 获取下一个交易日的因子值
    factorDF: pd.DataFrame = context["MyFactor"][context["MyFactor"]["date"]==nextDate].reset_index(drop=True)
    if factorDF.empty:
        return
    # 根据下一个交易日的因子值生成信号
    dayLongList: List[str] = factorDF[factorDF["value"]>=np.percentile(factorDF["value"], 95)]["symbol"].tolist()
    dayShortList: List[str] = factorDF[factorDF["value"]<=np.percentile(factorDF["value"], 5)]["symbol"].tolist()
    if len(dayLongList)>0:
        context["dayLongDict"] = dict(zip(dayLongList,[0.8/len(dayLongList)]*len(dayLongList)))
    if len(dayShortList)>0:
        context["dayShortDict"] = dict(zip(dayShortList,[0.4/len(dayShortList)]*len(dayShortList)))
    print("Current Backtest DayTime is", currentDate, currentTime)

def onTrade(self: BackTester, context: Context, trade: Dict[str, any]):
    """
    成交回报函数
    trade: {"timestamp":, "symbol":, "price":, "direction": }
    """
    print("OnTrade", trade["timestamp"], trade["symbol"], trade["price"], trade["direction"])

def onBar(self: BackTester, context: Context, msg: Dict[str, Dict[str, float]]):
    """
    Bar回调函数
    msg: {"标的1":{"open": "high": ...}}
    Rule-1: 如果下一个交易日是调仓日,则今日平掉所有仓位
    Rule-2: 如果当前交易日是调仓日,则进行买入
    """
    # 获取框架维护的基本属性 -> 时间
    currentDate: pd.Timestamp = context["TradeDate"]
    nextDate: pd.Timestamp = context["NextDate"]
    currentTimestamp: pd.Timestamp = context["TradeTime"]

    # Rule-1: 如果下一个交易日是调仓日, 则今日平掉所有仓位
    if nextDate in context["posDateList"]:
        longSummary: Dict[str,StockSummary] = self.getStockSummary(direction="long", symbol=None)
        shortSummary: Dict[str,StockSummary] = self.getStockSummary(direction="short", symbol=None)
        for symbol, summary in longSummary.items():
            if symbol not in msg:   # 说明没有该标的的K线
                continue
            vol = summary.total_vol
            price = msg[symbol]["open"]
            self.orderCloseStock(direction="long", symbol=symbol, vol=vol, price=price,
                                 min_order_timestamp=currentTimestamp,
                                 max_order_timestamp=currentTimestamp + pd.Timedelta(1, "D"),
                                 reason="closeLong", partial_order=False)
        # for symbol, summary in shortSummary.items():
        #     if symbol not in msg:   # 说明没有该标的的K线
        #         continue
        #     vol = summary.total_vol
        #     price = msg[symbol]["open"]
        #     self.orderCloseStock(...)

    # Rule-2: 如果当前交易日是调仓日, 则按信号进行买入
    if currentDate in context["posDateList"]:
        currentCash = self.getAvailableCash(assetType="stock")
        if currentCash <= self.SysContext.oriStockCash * 0.1:
            print("CurrentDate", currentDate, "Cash is not enough!", "CurrentCash: ", currentCash)
            return
        longSummary: Dict[str,StockSummary] = self.getStockSummary(direction="long", symbol=None)
        shortSummary: Dict[str,StockSummary] = self.getStockSummary(direction="short", symbol=None)
        for symbol, bar in msg.items():
            # 遍历当前每个股票的K线
            # 1.若没有触发日线信号 -> 自动结束
            if symbol not in context["dayLongDict"] and symbol not in context["dayShortDict"]:
                continue

            # 2.若当前有持仓 -> 自动结束
            # if symbol in longSummary or symbol in shortSummary:
            #     continue

            # 3.若触发了日线多单信号 -> 下多单
            if symbol in context["dayLongDict"]:
                price = msg[symbol]["open"]
                vol = int(currentCash * context["dayLongDict"][symbol]/ price)
                self.orderOpenStock("long", symbol, vol=vol, price=price,
                                    static_profit=0.02, static_loss=0.02,
                                    dynamic_profit=0.03, dynamic_loss=0.03,
                                    min_timestamp=nextDate, max_timestamp=pd.Timestamp(self.end_date),
                                    min_order_timestamp=currentTimestamp, max_order_timestamp=nextDate,
                                    commission=0.0, partial_order=False,
                                    reason="openLong")

            # # 4.若触发了日线空单信号 -> 下空单
            # if symbol in context["dayShortDict"]:
            #     price = msg[symbol]["open"]
            #     vol = int(currentCash * context["dayShortDict"][symbol]/ price)
            #     self.orderOpenStock(...)

def finalize(context: Context):
    """
    策略回调结束函数
    """
    print("Backtest Finalize!")

if __name__ == "__main__":
    # 获取配置文件
    session = ddb.session("172.16.0.184", 8001, "maxim", "dyJmoc-tiznem-1figgu")
    config = {
        "start_date": "20200101",
        "end_date": "20210101",
        "run_stock": True,
        "run_future": False,
        "freq": 2, # 1(分钟频) # 2(日频)
        "cash": 2000000,
        "stockCash": 1000000,
        "futureCash": 1000000
    }
    # MyFactor = session.run("""
    #     select symbol, date, value
    #     from loadTable("dfs://Dayfactor", "pt")
    #     where factor == "Test_lightgbm"
    #     and (date between 2020.01.01 and 2021.01.01) and !isNull(factor)
    # """)
    # MyFactor.to_feather(r"D:\BackTest\PyBackTest\data\stock_cn\factor\MyFactor.feather")
    MyFactor = pd.read_feather(r"D:\BackTest\PyBackTest\data\stock_cn\factor\MyFactor.feather")
    config["context"] = {
        "MyFactor": MyFactor,
        "dayLongDict": [],  # 每日做多列表
        "dayShortDict": [] # 每日做空列表
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
    BackTester = BackTester("StockStrategyTest", config, eventCallBacksDict, session=session)
    t0 = time.time()
    stockBar = pd.read_parquet(r"D:\BackTest\PyBackTest\data\stock_cn\bar")
    stockBar = stockBar[stockBar["TradeDate"]<=pd.Timestamp("20200131")].reset_index(drop=True)
    stockInfo = pd.read_parquet(r"D:\BackTest\PyBackTest\data\stock_cn\info")
    stockInfo = stockInfo[stockInfo["TradeDate"]<=pd.Timestamp("20200131")].reset_index(drop=True)
    BackTester.append(
        stockBar=stockBar,
        stockInfo=stockInfo,
        futureBar=None,
        futureInfo=None
    )
    # TODO: info对象缓存
    t1 = time.time()
    stats = BackTester.getTradeStatistics(statsType=None)
    orderDetails = BackTester.getOrderDetails(assetType="stock")
    tradeDetails = BackTester.getTradeDetails(assetType="stock")
    print(stats)
    stats.to_excel(r"Statistics.xlsx",index=None)
    orderDetails.to_excel(r"OrderDetails.xlsx",index=None)
    tradeDetails.to_excel(r"TradeDetails.xlsx",index=None)
    print("耗时:", t1-t0, "s")
