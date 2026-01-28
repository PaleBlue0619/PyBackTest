import os
import time
from src.entity.CounterBehavior import CounterBehavior
from src.entity.Counter import Counter
from src.entity.Context import Context
from src.entity.DataDict import DataDict
from src.service.getdata.fromDataFrame import fromDataFrame
from typing import Callable, List, Dict
import dolphindb as ddb # 使用其交易日历功能
import pandas as pd # 使用其时间戳
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
"""
策略封装模块:
config:Dict[str, any]
-必需属性:
"context":Dict[str,any]:行情上下文字典
"startDate":str:开始日期
"endDate":str:结束日期
"runStock": bool: 策略中是否包含股票
"runFuture": bool: 策略中是否包含期货
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
本质为了用户层友好: 用户层 -> BackTester <- 开发层(Counter) <- 底层逻辑(CounterBehavior)
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
        self.initialize()   # 创建回测引擎的时候进行初始化

    def initialize(self):
        """
        用户的初始化函数调用
        """
        # 系统的初始化 -> 构建context上下文
        self.SysContext = Context.get_instance()
        self.SysContext.initialize_from_config(config=self.config)  # 从用户传入的配置中初始化
        self.dataDict = DataDict.get_instance()
        self.UserContext["TradeDate"] = self.start_date
        self.UserContext["TradeTime"] = self.start_date
        self.UserContext["NextDate"] = self.date_list[min(1, len(self.date_list)-1)]

        if "initialize" in self.eventCallbacks:
            initialize_func = self.eventCallbacks["initialize"]
            initialize_func(self, self.UserContext)

    def beforeTrading(self):
        """
        用户级别的beforeTrading调用
        """
        if "beforeTrading" in self.eventCallbacks:
            beforeTrading_func = self.eventCallbacks["beforeTrading"]
            beforeTrading_func(self, self.UserContext)

    def onBar(self, barDict: Dict[str, any]):
        """
        用户级别的onBar调用
        """
        if "onBar" in self.eventCallbacks:
            onBar_func = self.eventCallbacks["onBar"]
            onBar_func(self, self.UserContext, barDict)

    def afterTrading(self):
        """
        用户的afterTrading调用
        """
        if "afterTrading" in self.eventCallbacks:
            afterTrading_func = self.eventCallbacks["afterTrading"]
            afterTrading_func(self, self.UserContext)

    def append(self, stockBar: pd.DataFrame = None, stockInfo: pd.DataFrame = None,
               futureBar: pd.DataFrame = None, futureInfo: pd.DataFrame = None):
        """
        由于技术能力有限 -> 这里默认回测到最大时间戳 -> 且以天为单位注入
        :param barData: 区间的Bar数据
        :param infoData: 区间的信息数据
        Step1. 转换为BarDict & InfoDict
        Step2. 提取其中的时间戳+排序 -> for loop进行回测
        """
        date_list = []
        def process_stockBar():
            """处理股票Bar"""
            if stockBar is None:
                return {}
            t0 = time.time()
            if self.config["freq"] == "minute":
                stockBarDict = fromDataFrame(stockBar).toStockBars(True, "TradeDate", "symbol", "open", "high",
                                                                   "low", "close", "volume", "TradeTime")
            else:
                stockBarDict = fromDataFrame(stockBar).toStockBars(False, "TradeDate", "symbol", "open", "high",
                                                                   "low", "close", "volume", None)
            t1 = time.time()
            print(f"{self.name} process_stockBar time: {t1-t0}")
            return stockBarDict

        def process_stockInfo():
            """处理股票Info"""
            if stockInfo is None:
                return {}
            t0 = time.time()
            stockInfoDict = fromDataFrame(stockInfo).toStockInfos("TradeDate", "symbol", "open_price", "high_price",
                                                                  "low_price", "close_price")
            t1 = time.time()
            print(f"{self.name} process_stockInfo time: {t1-t0}")
            return stockInfoDict

        def process_futureBar():
            """处理期货Bar"""
            if futureBar is None:
                return {}
            t0 = time.time()
            if self.config["freq"] == "minute":
                futureBarDict = fromDataFrame(futureBar).toFutureBars(True, "TradeDate", "symbol", "open", "high",
                                                                      "low", "close", "volume", "TradeTime")
            else:
                futureBarDict = fromDataFrame(futureBar).toFutureBars(False, "TradeDate", "symbol", "open", "high",
                                                                      "low", "close", "volume", None)
            t1 = time.time()
            print(f"{self.name} process_futureBar time: {t1-t0}")
            return futureBarDict

        def process_futureInfo():
            """处理期货Info"""
            if futureInfo is None:
                return {}
            t0 = time.time()
            futureInfoDict = fromDataFrame(futureInfo).toFutureInfos(
                    "TradeDate", "symbol", "open_price", "high_price", "low_price",
                    "close_price", "pre_settle", "settle", "multi", "start_date", "end_date")
            t1 = time.time()
            print(f"{self.name} process_futureInfo time: {t1-t0}")
            return futureInfoDict

        # 并行执行
        with ThreadPoolExecutor(max_workers=2) as executor:
            # 提交任务
            stockBarThread = executor.submit(process_stockBar) if stockBar is not None else None
            stockInfoThread = executor.submit(process_stockInfo) if stockInfo is not None else None
            futureBarThread = executor.submit(process_futureBar) if futureBar is not None else None
            futureInfoThread = executor.submit(process_futureInfo) if futureInfo is not None else None

            # 等待结果
            if self.SysContext.run_stock and stockInfoThread and stockBarThread:
                stockInfoDict = stockInfoThread.result()
                stockBarDict = stockBarThread.result()
                date_list += list(stockBarDict.keys())
            else:
                stockBarDict, stockInfoDict = {}, {}
            if self.SysContext.run_future and futureInfoThread and futureBarThread:
                futureInfoDict = futureInfoThread.result()
                futureBarDict = futureBarThread.result()
                date_list += list(futureBarDict.keys())
            else:
                futureBarDict, futureInfoDict = {}, {}

        date_list = sorted(set(date_list))
        for i in range(0, len(date_list)):
            date = date_list[i]
            # 0.更新相关属性 -> 包括用户级别Context中的属性
            self.SysContext.current_date = date
            self.UserContext["TradeDate"] = date
            self.UserContext["TradeTime"] = date
            nextDateIdx = min(len(date_list)-1, i+1)
            self.UserContext["NextDate"] = self.date_list[nextDateIdx]

            # 1.设置该日数据
            if self.SysContext.run_stock and date in stockBarDict:
                self.dataDict.set_stockKDict(stockBarDict[date])
                self.dataDict.set_stockInfoDict(stockInfoDict[date])
            if self.SysContext.run_future and date in futureBarDict:
                self.dataDict.set_futureKDict(futureBarDict[date])
                self.dataDict.set_futureInfoDict(futureInfoDict[date])

            # 2.执行系统级别beforeTrading回调 -> 用户级别beforeTrading回调
            if self.SysContext.run_future:
                self.beforeDayFuture()
            self.beforeTrading()

            # 3.执行分钟频回测
            minute_list = []
            if date in stockBarDict:
                minute_list += list(stockBarDict[date].keys())
            if date in futureBarDict:
                minute_list += list(futureBarDict[date].keys())
            minute_list = sorted(set(minute_list))

            for minute in minute_list:
                # 设置时间格式
                self.SysContext.current_minute = minute
                self.SysContext.current_timestamp = minute
                self.UserContext["TradeTime"] = minute

                # 3. 执行用户级别onBar回调[核心]
                barDict = dict() # 需要传入onBar的参数
                if date in stockBarDict and minute in stockBarDict[date]:
                    barDict.update(stockBarDict[date][minute])
                if date in futureBarDict and minute in futureBarDict[date]:
                    barDict.update(futureBarDict[date][minute])
                self.onBar(barDict)
                if self.SysContext.run_stock:
                    self.processStockOrder(1.0, 1.0)
                    self.afterBarStock()
                    self.monitorStockPosition("long", False, useClose=False)
                    self.monitorStockPosition("short", True, useClose=False)

                if self.SysContext.run_future:
                    self.processFutureOrder(1.0, 1.0)
                    self.afterBarFuture()
                    self.monitorFuturePosition("long", False, useClose=False)
                    self.monitorFuturePosition("short", True, useClose=False)

            # 4.执行用户级别afterTrading回调 -> 系统级别afterTrading回调
            self.afterTrading()
            if self.SysContext.run_stock:
                self.afterDayStock()
            if self.SysContext.run_future:
                self.afterDayFuture()
            # 5.统计今日盈亏
            self.afterDayStats()