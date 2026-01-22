import os
from src.entity.CounterBehavior import CounterBehavior
from src.entity.Counter import Counter
from src.entity.Context import Context
from src.entity.DataDict import DataDict
from src.service.getdata.fromDataFrame import fromDataFrame
from typing import Callable, List, Dict
import dolphindb as ddb # 使用其交易日历功能
import pandas as pd # 使用其时间戳
from tqdm import tqdm
"""
策略封装模块:
config:Dict[str, any]
-必需属性:
"context":Dict[str,any]:行情上下文字典
"startDate":str:开始日期
"endDate":str:结束日期
"hasStock": bool: 策略中是否包含股票
"hasFuture": bool: 策略中是否包含期货
"stockBarPath": str
"stockInfoPath": str
"futureBarPath": str
"futureInfoPath": str

eventCallbacks:Dict[str, callable]

initialize(mutable context): 策略初始化回调函数

onTrade(mutable context): 成交回调函数

onBar(mutable context): Bar回调函数

beforeTrading(mutable context): 盘前回调函数

afterTrading(mutable context): 盘后回调函数

finalize(mutable context): 策略结束回调函数
"""

"""
回测引擎类 —> 思路借鉴DolphinDB Backtest 回测插件
https://docs.dolphindb.cn/zh/plugins/backtest/interface_description.html
"""
class BackTester(Counter, CounterBehavior):
    def __init__(self, name:str, config:Dict[str, any], eventCallbacks:Dict[str, Callable], session:ddb.session):
        self.name = name
        self.config = config
        self.UserContext = config["context"] # 用户级别上下文字典
        self.eventCallbacks = eventCallbacks
        self.SysContext:Context = None   # 系统级别上下文字典
        self.dataDict:DataDict = None  # 行情字典
        self.start_date = config["start_date"]
        self.end_date = config["end_date"]
        self.date_list = session.run(f"""
        startDate = {pd.Timestamp(self.start_date).strftime("%Y.%m.%d")}
        endDate = {pd.Timestamp(self.end_date).strftime("%Y.%m.%d")}
        table(getMarketCalendar("CFFEX",startDate,endDate) as `tradeDay)
        """)["tradeDay"].tolist()
        self.initialize(self.UserContext)   # 创建回测引擎的时候进行初始化

    def initialize(self, contextDict):
        """
        先执行系统的初始化 -> 再执行用户的初始化函数
        """
        # 系统的初始化 -> 构建context上下文
        self.SysContext = Context.get_instance()
        self.SysContext.initialize_from_config(config=self.config)  # 从用户传入的配置中初始化
        self.dataDict = DataDict.get_instance()

        if "initialize" in self.eventCallbacks:
            initialize_func = self.eventCallbacks["initialize"]
            initialize_func(self.UserContext)

    def beforeTrading(self):
        """
        先执行系统的beforeTrading -> 再执行用户的beforeTrading
        """
        if "beforeTrading" in self.eventCallbacks:
            beforeTrading_func = self.eventCallbacks["beforeTrading"]
            beforeTrading_func(self.UserContext)

    def onBar(self, contextDict):
        """
        先执行系统的onBar -> 再执行用户的onBar
        """
        if "onBar" in self.eventCallbacks:
            onBar_func = self.eventCallbacks["onBar"]
            onBar_func(self, self.UserContext)

    def afterTrading(self):
        """
        先执行系统的afterTrading -> 再执行用户的afterTrading
        """
        if "afterTrading" in self.eventCallbacks:
            afterTrading_func = self.eventCallbacks["afterTrading"]
            afterTrading_func(self.UserContext)

    def append(self, dataType: str, barData: pd.DataFrame, infoData: pd.DataFrame):
        """
        由于技术能力有限 -> 这里默认回测到最大时间戳 -> 且以天为单位注入
        :param dataType: stock/future -> 股票数据 | 期货数据
        :param barData: 区间的Bar数据
        :param infoData: 区间的信息数据
        :return:
        """
        if dataType == "stock":
            if self.config["freq"] == "minute": # 分钟频数据
                stockBarDict = fromDataFrame(barData).toStockBars(True, "TradeDate", "symbol", "open", "high", "low", "close", "volume", "TradeTime")
            else:
                stockBarDict = fromDataFrame(barData).toStockBars(False, "TradeDate", "symbol", "open", "high", "low", "close", "volume", None)
            stockInfoDict = fromDataFrame(infoData).toStockInfo("TradeDate", "symbol", "open_price", "high_price", "low_price", "close_price", "start_date", "end_date")
        else:
            if self.config["freq"] == "minute": # 分钟频数据
                futureBarDict = fromDataFrame(barData).toFutureBars(True, "TradeDate", "symbol", "open", "high", "low", "close", "volume", "TradeTime")
            else:
                futureBarDict = fromDataFrame(barData).toFutureBars(False, "TradeDate", "symbol", "open", "high", "low", "close", "volume", None)
            futureInfoDict = fromDataFrame(infoData).toFutureInfo("tradeDate", "symbol", "open_price", "high_price", "low_price", "close_price", "pre_settle", "settle", "start_date", "end_date")
        # 获取当前的时间戳 -> 即上一次回测的时间戳


    # def run(self):
    #     """
    #     核心策略执行函数
    #     """
    #     # Step1. 初始化
    #     self.initialize(self.config["context"])
    #
    #     # Step2.根据时间戳for loop
    #     for i in tqdm(range(0, len(self.date_list))):
    #         self.SysContext.current_date = self.date_list[i]
    #         # Step2.1 获取该日数据 -> 设置数据
    #         if self.SysContext.run_stock:   # 需要设置股票的数据
    #             barPath = os.path.join(self.SysContext.stockBarPath, self.SysContext.current_date.strftime("%Y%m%d") + ".pqt")
    #             infoPath = os.path.join(self.SysContext.stockInfoPath, self.SysContext.current_date.strftime("%Y%m%d") + ".pqt")
    #             if not os.path.exists(barPath) or not os.path.exists(infoPath):
    #                 continue
    #             stockBarDict = fromDataFrame(pd.read_parquet(barPath)).toStockBar(False, "TradeDate", "symbol", "open", "high", "low",
    #                                                            "close", "volume", None)
    #             stockInfoDict = fromDataFrame(pd.read_parquet(infoPath)).toStockInfo("TradeDate", "symbol", "open_price", "high_price",
    #                                                               "low_price", "close_price", "start_date", "end_date")
    #             self.dataDict.set_stockKDict(stockBarDict)
    #             self.dataDict.set_stockInfoDict(stockInfoDict)
    #
    #         if self.SysContext.run_future: # 需要设置期货的数据
    #             barPath = os.path.join(self.SysContext.futureBarPath, self.SysContext.current_date.strftime("%Y%m%d") + ".pqt")
    #             infoPath = os.path.join(self.SysContext.futureInfoPath, self.SysContext.current_date.strftime("%Y%m%d") + ".pqt")
    #             if not os.path.exists(barPath) or not os.path.exists(infoPath):
    #                 continue
    #             futureBarDict = fromDataFrame(pd.read_parquet(barPath)).toFutureBar(False, "TradeDate", "symbol", "open", "high", "low", "close", "volume", None)
    #             futureInfoDict = fromDataFrame(pd.read_parquet(infoPath)).toFutureInfo("tradeDate", "symbol", "open_price", "high_price", "low_price", "close_price",
    #                                                                 "pre_settle", "settle", "start_date", "end_date")
    #             self.dataDict.set_futureKDict(futureBarDict)
    #             self.dataDict.set_futureInfoDict(futureInfoDict)
    #
    #         # Step2.2 执行系统级别beforeTrading回调 -> 用户级别beforeTrading回调
    #         if self.SysContext.run_future:
    #             self.beforeDayFuture()
    #         self.beforeTrading()
    #
    #         # Step2.3 执行用户级别onBar回调[核心]
    #         self.onBar(self.UserContext)
    #
    #         # Step2.4 执行
