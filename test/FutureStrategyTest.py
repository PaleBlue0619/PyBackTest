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
    # print("Initialize context", context)
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

# TODO: 待实现成交回报函数的回调逻辑
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
        longSummary: Dict[str,FutureSummary] = self.getFutureSummary(direction="long", symbol=None)
        shortSummary: Dict[str,FutureSummary] = self.getFutureSummary(direction="short", symbol=None)
        for symbol, summary in longSummary.items():
            if symbol not in msg:
                continue
            vol = summary.total_vol
            price = msg[symbol]["open"]
            self.orderCloseFuture(direction="long", symbol=symbol, vol=vol, price=price,
                                  min_order_timestamp=currentTimestamp,
                                  max_order_timestamp=currentTimestamp + pd.Timedelta(1, "D"),
                                  reason="closeLong", partial_order=False)
        for symbol, summary in shortSummary.items():
            if symbol not in msg:
                continue
            vol = summary.total_vol
            price = msg[symbol]["open"]
            self.orderCloseFuture(direction="short", symbol=symbol, vol=vol, price=price,
                                  min_order_timestamp=currentTimestamp,
                                  max_order_timestamp=currentTimestamp + pd.Timedelta(1, "D"),
                                  reason="closeShort", partial_order=False)

    # Rule-2: 如果当前交易日是调仓日, 则按照信号进行开仓
    if currentDate in context["posDateList"]:
        currentCash = self.getAvailableCash(assetType="future")
        oriCash = self.SysContext.oriFutureCash
        if currentCash <= self.SysContext.oriFutureCash * 0.1:
            print("CurrentDate", currentDate, "Cash is not enough!", "CurrentCash: ", currentCash)
            return
        longSummary: Dict[str,FutureSummary] = self.getFutureSummary(direction="long", symbol=None)
        shortSummary: Dict[str,FutureSummary] = self.getFutureSummary(direction="short", symbol=None)
        for symbol, bar in msg.items():
            # 遍历当前每个期货的K线
            # 1.若没有触发日线信号 -> 自动结束
            if symbol not in context["dayLongDict"] and symbol not in context["dayShortDict"]:
                continue

            # 2.若当前有持仓 -> 自动结束
            if symbol in longSummary or symbol in shortSummary:
                continue

            contract = str(symbol).split(".")[0]
            product = contract.replace(contract[-4:],"")
            multi = context["MultiDict"][product]   # 获取交易乘数
            # 3.若触发了日线多单信号 -> 下多单
            if symbol in context["dayLongDict"]:
                price = msg[symbol]["open"]
                margin_rate = 0.1
                vol = max(int(oriCash * context["dayLongDict"][symbol]/ margin_rate / price),1)
                vol -= vol % multi
                self.orderOpenFuture(direction="long", symbol=symbol, vol=vol, price=price,
                                     commission=0.0,
                                     static_profit=0.015, static_loss=0.01,
                                     dynamic_profit=0.015, dynamic_loss=0.01,
                                     min_timestamp=currentTimestamp, max_timestamp=pd.Timestamp("20201231"),
                                     min_order_timestamp=currentTimestamp, max_order_timestamp=currentTimestamp + pd.Timedelta(1, "D"),
                                     reason="openLong", partial_order=False)
            # # 4.若触发了日线空单信号 -> 下空单
            # if symbol in context["dayShortDict"]:
            #     price = msg[symbol]["open"]
            #     margin_rate = 0.1
            #     vol = max(int(oriCash * context["dayShortDict"][symbol]/ margin_rate / price),1)
            #     vol -= vol % multi
            #     self.orderOpenFuture(direction="short", symbol=symbol, vol=vol, price=price,
            #                          commission=0.0,
            #                          static_profit=0.015, static_loss=0.01,
            #                          dynamic_profit=0.015, dynamic_loss=0.01,
            #                          min_timestamp=currentTimestamp, max_timestamp=pd.Timestamp("20201231"),
            #                          min_order_timestamp=currentTimestamp, max_order_timestamp=currentTimestamp + pd.Timedelta(1, "D"),
            #                          reason="openShort", partial_order=False)

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

    # 获取下一日的主力合约信息
    if nextDate not in context["MainContractDict"]:
        return
    MainContractDict = context["MainContractDict"][nextDate]
    if "AU" in MainContractDict:
        context["dayLongDict"] = {MainContractDict["AU"][0]: 0.4}
    if "SC" in MainContractDict:
        context["dayShortDict"] = {MainContractDict["SC"][0]: 0.4}

def finalize(context: Context):
    """
    策略回调结束函数
    """
    print("Backtest Finalize!")


if __name__ == "__main__":
    # 这是一个很SB的策略 -> 无脑做空原油主连+做多黄金主连
    # TODO: 补充交易乘数
    # 获取配置文件
    session = ddb.session("172.16.0.184", 8001, "maxim", "dyJmoc-tiznem-1figgu")
    config = {
        "start_date": "20200101",
        "end_date": "20210101",
        "run_stock": False,
        "run_future": True,
        "freq": 2, # 1(分钟频) # 2(日频)
        "cash": 2000000,
        "stockCash": 1000000,
        "futureCash": 1000000
    }  # 主力合约列表
    MainContract = pd.read_feather(r"D:\BackTest\PyBackTest\data\future_cn\main\mainContract.feather")
    # symbol_info = {}
    # for symbol, group in MainContract.groupby('symbol'):
    #     symbol_info[symbol] = {'startDate': group['TradeDate'].min(),'endDate': group['TradeDate'].max()}
    # MainContractDict = {     # 一次性构建嵌套字典
    #     date: {
    #         product: [
    #             symbol,
    #             symbol_info[symbol]['startDate'],
    #             symbol_info[symbol]['endDate']
    #         ]
    #         for product, symbol in zip(group['product'], group['symbol'])
    #     }
    #     for date, group in MainContract.groupby('TradeDate')
    # }
    # np.save(r"D:\BackTest\PyBackTest\data\future_cn\main\MainContractDict.npy", MainContractDict, allow_pickle=True)
    MainContractDict = np.load(r"D:\BackTest\PyBackTest\data\future_cn\main\MainContractDict.npy", allow_pickle=True).item()
    config["context"] = {
        "MainContractDict": MainContractDict, # {TradeDate:{product: symbol}}
        "MultiDict": {"AU":1000, "SC":1000}, # 交易乘数
        "dayLongDict": {},  # 每日做多字典{标的: 权重}
        "dayShortDict": {}  # 每日做空字典{标的: 权重}
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
    BackTester = BackTester("FutureBackTest", config,
                            eventCallBacksDict,
                            session=session)
    futureBar = pd.read_parquet(r"D:\BackTest\PyBackTest\data\future_cn\bar")
    futureInfo = pd.read_parquet(r"D:\BackTest\PyBackTest\data\future_cn\info").rename(columns={"tradeDate":"TradeDate"})
    futureInfo["multi"] = futureInfo["symbol"].apply(lambda x:str(x)[:2]).map({"SC":1000, "AU":1000})
    t0 = time.time()
    BackTester.append(
        stockBar=None,
        stockInfo=None,
        futureBar=futureBar,
        futureInfo=futureInfo
    )
    # TODO: info对象缓存
    t1 = time.time()
    stats = BackTester.getTradeStatistics(statsType=None)
    orderDetails = BackTester.getOrderDetails(assetType="future")
    tradeDetails = BackTester.getTradeDetails(assetType="future")
    print(stats)
    stats.to_excel(r"Statistics(Future).xlsx", index=None)
    orderDetails.to_excel(r"OrderDetails(Future).xlsx", index=None)
    tradeDetails.to_excel(r"TradeDetails(Future).xlsx", index=None)
    print("耗时:", t1-t0, "s")
