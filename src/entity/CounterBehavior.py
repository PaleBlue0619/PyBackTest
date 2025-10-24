import pandas as pd
import Context
import DataDict
from TradeBehavior import TradeBehavior
from src.entity.pojo.Order import *
from src.entity.pojo.Info import *
from src.entity.pojo.Position import *
from typing import Dict, List, Tuple

class CounterBehavior(TradeBehavior):
    def __init__(self):
        super(CounterBehavior, self).__init__()

    def beforeDayFuture(self):
        """更新保证金率至各个仓位->实行资金划拨"""
        # 获取回测上下文实例
        context = Context.get_instance()
        dataDict = DataDict.get_instance()

        # 获取当前品种信息
        futureInfo: Dict[str, FutureInfo] = dataDict.futureInfoDict

        cashDiff = 0.0 # 需要从现金账户中扣除的资金余额/ 负数表示从仓位的保证金属性中还回来的余额
        longPos: Dict[str, FuturePosition] = context.futureLongPosition
        shortPos: Dict[str, FuturePosition] = context.futureShortPosition
        for symbol in longPos:
            cashDiff += longPos[symbol].marginRateUpdate(futureInfo[symbol].margin_rate)
        for symbol in shortPos:
            cashDiff += shortPos[symbol].marginRateUpdate(futureInfo[symbol].margin_rate)

        # 更新当前资金
        context.futureCash -= cashDiff
        context.cash -= cashDiff

    def afterBarStock(self):
        """行情更新对股票相关属性的影响:
        1.变全局属性：仓位动态盈亏
        2.变持仓视图：realTimePrice & realTimeProfit
        3.变自身仓位：history_min/max + profit + pre_price
        """
        # 获取回测上下文实例
        context = Context.get_instance()

        # 获取当前K线
        minute = context.current_minute
        dataDict = DataDict.get_instance()
        barDict = dataDict.stockKDict[minute]
        infoDict = dataDict.stockInfoDict[minute]

        # 获取持仓 & 持仓视图
        stockLongPos: Dict[str, StockPosition] = context.stockLongPosition
        stockShortPos: Dict[str, StockPosition] = context.stockShortPosition

        for symbol in stockLongPos:
            if symbol in infoDict:
                end_date = infoDict[symbol].end_date
                daily_high_price = barDict[symbol][end_date].high
                daily_low_price = barDict[symbol][end_date].low