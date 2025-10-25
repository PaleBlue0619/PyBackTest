import pandas as pd
from Context import Context
import DataDict
from TradeBehavior import TradeBehavior
from src.entity.pojo.Order import *
from src.entity.pojo.Info import *
from src.entity.pojo.Position import *
from src.entity.pojo.Summary import *
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

        cashDiff = 0.0  # 需要从现金账户中扣除的资金余额/ 负数表示从仓位的保证金属性中还回来的余额
        longPos: Dict[str, List[FuturePosition]] = context.futureLongPosition
        shortPos: Dict[str, List[FuturePosition]] = context.futureShortPosition
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
        day = context.current_date
        minute = context.current_minute
        timestamp = context.current_timestamp
        dataDict = DataDict.get_instance()
        barDict: Dict = dataDict.stockKDict[minute]
        infoDict: Dict[str, StockInfo] = dataDict.stockInfoDict[day]

        # 获取持仓 & 持仓视图
        stockLongPos: Dict[str, List[StockPosition]] = context.stockLongPosition
        stockShortPos: Dict[str, List[StockPosition]] = context.stockShortPosition

        # 合并处理多空仓位
        for position_dict, summary_dict in [(stockLongPos, context.stockLongSummary),
                                            (stockShortPos, context.stockShortSummary)]:
            for symbol in position_dict:
                if symbol in infoDict:
                    end_date = infoDict[symbol].end_date
                    daily_high_price = barDict[symbol]["high"]
                    daily_low_price = barDict[symbol]["low"]
                else:
                    end_date = context.end_date
                    daily_high_price = None
                    daily_low_price = None

                if symbol not in barDict:
                    continue

                close = barDict[symbol]["close"]

                # 1. 更新持仓视图
                summary_dict[symbol].onBarUpdate(close)
                # 2.更新仓位
                posList: List[StockPosition] = position_dict.get(symbol)
                for pos in posList:
                    # 更新Monitor
                    pos.onBarMonitorTime(current_timestamp=timestamp, current_date=day, end_date=end_date)
                    pos.onBarMonitorStatic(daily_high_price=daily_high_price, daily_low_price=daily_low_price)
                    pos.onBarMonitorDynamic(daily_high_price=daily_high_price, daily_low_price=daily_low_price)
                    # 更新仓位基本属性
                    realTimeProfit = position_dict[symbol].onBarUpdate(close)
                    # 更新当前实时盈亏
                    context.realTimeProfit += realTimeProfit
                    context.stockRealTimeProfit += realTimeProfit

    def afterBarFuture(self):
        """行情更新对期货相关属性的影响
        1.变全局属性：仓位动态盈亏
        2.变持仓视图：realTimePrice & realTimeProfit
        3.变自身仓位：history_min/max + profit + pre_price
        """
        # 获取回测上下文实例
        context = Context.get_instance()

        # 获取当前K线
        day = context.current_date
        minute = context.current_minute
        timestamp = context.current_timestamp
        dataDict = DataDict.get_instance()
        barDict: Dict = dataDict.stockKDict[minute]
        infoDict: Dict[str, StockInfo] = dataDict.stockInfoDict[day]

        # 获取持仓 & 持仓视图
        futureLongPos: Dict[str, List[FuturePosition]] = context.futureLongPosition
        futureShortPos: Dict[str, List[FuturePosition]] = context.futureShortPosition

        # 合并处理多空仓位
        for position_dict, summary_dict in [(futureLongPos, context.futureLongSummary),
                                            (futureShortPos, context.futureShortSummary)]:
            for symbol in position_dict:
                if symbol in infoDict:
                    end_date = infoDict[symbol].end_date
                    daily_high_price = barDict[symbol]["high"]
                    daily_low_price = barDict[symbol]["low"]
                else:
                    end_date = context.end_date
                    daily_high_price = None
                    daily_low_price = None

                if symbol not in barDict:
                    continue

                close = barDict[symbol]["close"]

                # 1. 更新持仓视图
                summary_dict[symbol].onBarUpdate(close)
                # 2.更新仓位
                posList: List[FuturePosition] = position_dict.get(symbol)
                for pos in posList:
                    # 更新Monitor
                    pos.onBarMonitorTime(current_timestamp=timestamp, current_date=day, end_date=end_date)
                    pos.onBarMonitorStatic(daily_high_price=daily_high_price, daily_low_price=daily_low_price)
                    pos.onBarMonitorDynamic(daily_high_price=daily_high_price, daily_low_price=daily_low_price)
                    # 更新仓位基本属性
                    realTimeProfit = position_dict[symbol].onBarUpdate(close)
                    # 更新当前实时盈亏
                    context.realTimeProfit += realTimeProfit
                    context.futureRealTimeProfit += realTimeProfit

    def afterDayStock(self):
        """重置仓位的monitor属性"""
        context = Context.get_instance()
        for symbol in context.stockLongPosition:
            posList: List[StockPosition] = context.stockLongPosition.get(symbol)
            for pos in posList:
                pos.afterDayUpdate()
        for symbol in context.stockShortPosition:
            posList: List[StockPosition] = context.stockShortPosition.get(symbol)
            for pos in posList:
                pos.afterDayUpdate()

    def afterDayFuture(self):
        """
        1. 重置仓位的monitor(time_monitor/static_monitor/dynamic_monitor)
        2. pre_price -> 设置为settle
        3. 计算margin & profit -> 更新仓位 & 持仓视图
        """
        # 获取回测上下文实例
        context = Context.get_instance()
        dataDict = DataDict.get_instance()
        infoDict: Dict[str, FutureInfo] = dataDict.futureInfoDict

        # 多空仓位合并处理
        for position_dict, summary_dict in [(context.futureLongPosition, context.futureLongSummary),
                                            (context.futureShortPosition, context.futureShortSummary)]:
            for symbol in position_dict:
                posList: List[FuturePosition] = position_dict.get(symbol)
                # 获取这个标的的settle
                if symbol not in infoDict:
                    continue
                settle = infoDict[symbol].settle  # 获取结算价
                summary_dict[symbol].afterDayUpdate(settle)
                for pos in posList:
                    realTimeProfit = pos.afterDayUpdate(settle)
                    settleProfit = pos.afterDaySettle(settle)
                    context.realTimeProfit += realTimeProfit
                    context.futureRealTimeProfit += realTimeProfit
                    context.futureSettleProfit += settleProfit

    def openStock(self, direction: str, symbol: str, vol: int, price: float,
                  static_profit: float, static_loss: float,
                  dynamic_profit: float, dynamic_loss: float,
                  min_timestamp: pd.Timestamp, max_timestamp: pd.Timestamp,
                  reason: str):
        """
        股票开仓/加仓
        """
        context = Context.get_instance()
        context.cash -= vol * price
        context.stockCash -= vol * price

        # 初始化视图对象
        pos = StockPosition(direction, symbol, price, vol,
                            min_timestamp, max_timestamp,
                            static_profit, static_loss,
                            dynamic_profit, dynamic_loss
                            )
        if direction == "long":
            if symbol not in context.stockLongPosition:  # 说明没有该股票多头的持仓
                context.stockLongPosition[symbol] = []
            context.stockLongPosition.append(pos)
            # 初始化Summary对象
            if symbol not in context.stockLongSummary:  # 说明没有该股票多头的持仓视图
                context.stockLongSummary[symbol] = StockSummary(direction, ori_price=price,
                                                                total_vol=vol,
                                                                static_profit=static_profit,
                                                                static_loss=dynamic_loss,
                                                                dynamic_profit=dynamic_profit,
                                                                dynamic_loss=dynamic_loss)
            else:
                context.stockLongSummary[symbol].openUpdate(price, vol, static_profit, static_loss,
                                                            dynamic_profit, dynamic_loss)
        else:
            if symbol not in context.stockShortPosition:  # 说明没有该股票多头的持仓
                context.stockShortPosition[symbol] = []
            context.stockShortPosition.append(pos)
            # 初始化Summary对象
            if symbol not in context.stockShortSummary:  # 说明没有该股票多头的持仓视图
                context.stockShortSummary[symbol] = StockSummary(direction, ori_price=price,
                                                                 total_vol=vol,
                                                                 static_profit=static_profit,
                                                                 static_loss=dynamic_loss,
                                                                 dynamic_profit=dynamic_profit,
                                                                 dynamic_loss=dynamic_loss)
            else:
                context.stockShortSummary[symbol].openUpdate(price, vol, static_profit, static_loss,
                                                             dynamic_profit, dynamic_loss)
        # TODO: 记录

    def openFuture(self, direction: str, symbol: str, vol: int, price: float,
                   static_profit: float, static_loss: float,
                   dynamic_profit: float, dynamic_loss: float,
                   min_timestamp: pd.Timestamp, max_timestamp: pd.Timestamp,
                   reason: str):
        """
        期货开仓/加仓
        """

        # 获取回测上下文实例
        context = Context.get_instance()
        dataDict = DataDict.get_instance()
        futureInfo = dataDict.futureInfoDict

        if symbol not in futureInfo:
            print(f"期货合约信息字典中不存在该期货合约:{symbol}")
            return
        margin_rate = futureInfo[symbol]["margin_rate"]
        context.cash -= vol * price * margin_rate
        context.stockCash -= vol * price * margin_rate
        pos = FuturePosition(direction, symbol, price, vol, margin_rate,
                             min_timestamp, max_timestamp,
                             static_profit, static_loss,
                             dynamic_profit, dynamic_loss
                             )
        if direction == "long":
            if symbol not in context.futureLongPosition:  # 说明没有该期货多头的持仓
                context.futureLongPosition[symbol] = []
            context.futureLongPosition.append(pos)
            # 初始化Summary对象
            if symbol not in context.futureLongPosition:  # 说明没有该股票多头的持仓视图
                context.futureLongPosition[symbol] = FutureSummary(direction, ori_price=price,
                                                                   total_vol=vol,
                                                                   static_profit=static_profit,
                                                                   static_loss=dynamic_loss,
                                                                   dynamic_profit=dynamic_profit,
                                                                   dynamic_loss=dynamic_loss)
            else:
                context.futureLongSummary[symbol].openUpdate(price, vol, static_profit, static_loss,
                                                             dynamic_profit, dynamic_loss)
        else:
            if symbol not in context.futureShortPosition:  # 说明没有该期货多头的持仓
                context.futureShortPosition[symbol] = []
            context.futureShortPosition.append(pos)
            # 初始化Summary对象
            if symbol not in context.futureShortPosition:  # 说明没有该股票多头的持仓视图
                context.futureShortPosition[symbol] = FutureSummary(direction, ori_price=price,
                                                                    total_vol=vol,
                                                                    static_profit=static_profit,
                                                                    static_loss=dynamic_loss,
                                                                    dynamic_profit=dynamic_profit,
                                                                    dynamic_loss=dynamic_loss)
            else:
                context.futureLongSumfutureShortPositionmary[symbol].openUpdate(price, vol, static_profit, static_loss,
                                                                                dynamic_profit, dynamic_loss)
        # TODO: 记录

    def closeStock(self, direction: str, symbol: str, price: float, vol: int,
                   reason: str):
        """
        股票平仓
        """
        profit = 0.0
        profitDiff = 0.0  # 相对于上一个K线的额外盈亏 -> 计入realTimeProfit
        margin = 0.0
        context = Context.get_instance()
        if direction == "long":
            if symbol not in context.stockLongPosition:
                print(f"没有该股票多头的持仓:{symbol}")
                return
            pos_list: List[StockPosition] = context.stockLongPosition[symbol]
        else:
            if symbol not in context.stockShortPosition:
                print(f"没有该股票空头的持仓:{symbol}")
                return
            pos_list: List[StockPosition] = context.stockShortPosition[symbol]

        sign_list = []
        current_vol_list = []
        ori_price_list = []
        pre_price_list = []
        time_monitor_list = []
        for pos in pos_list:
            sign_list.append(pos.sign)
            current_vol_list.append(pos.vol)
            ori_price_list.append(pos.ori_price)
            pre_price_list.append(pos.pre_price)
            time_monitor_list.append(pos.time_monitor)
        # 获取允许平仓的最大数量
        state = True
        if -2 in time_monitor_list:
            state = False
            index = time_monitor_list.index(-2)
            current_vol = sum(current_vol_list[:index])
        else:
            current_vol = sum(current_vol_list)
        # 获取平仓的最终数量
        max_vol = min(current_vol, vol)
        record_vol = max_vol  # for record
        if max_vol >= current_vol and state:  # 全部平仓
            for i in range(0, len(pos_list)):
                margin += price * current_vol_list[i]  # 收回的现金
                profit += (price - ori_price_list[i]) * current_vol_list[i] * sign_list[i]
                profitDiff += (price - pre_price_list[i]) * current_vol_list[i] * sign_list[i]

            # 再对持仓&持仓视图进行批处理
            if direction == "long":
                del context.stockLongSummary[symbol]  # 直接删除该标的的持仓视图
                del context.stockLongPosition[symbol]  # 直接删除该标的的持仓
            else:
                del context.stockShortSummary[symbol]
                del context.stockShortPosition[symbol]

        else:  # 部分平仓
            # 先对视图进行批处理
            if direction == "long":
                context.stockLongSummary[symbol].closeUpdate(price, max_vol)
            else:
                context.stockShortSummary[symbol].closeUpdate(price, max_vol)
            for i in range(0, len(pos_list)):
                posVol = current_vol_list[i]
                oriPrice = ori_price_list[i]
                prePrice = pre_price_list[i]
                posSign = sign_list[i]
                if max_vol >= posVol:  # 当前仓位能够全部平仓
                    margin += price * posVol
                    profit += (price - oriPrice) * posVol * posSign
                    profitDiff += (price - prePrice) * posVol * posSign
                    pos_list.pop(i)
                    max_vol -= posVol
                else:  # 当前仓位部分平仓
                    pos_list[0].vol -= max_vol
                    margin += price * max_vol
                    profit += (price - oriPrice) * max_vol * posSign
                    profitDiff += (price - prePrice) * max_vol * posSign
                    break

        # 结算
        context.cash += (margin + profit)  # 收回的100%保证金
        context.stockCash += (margin + profit)
        context.profit += profit
        context.stockProfit += profit
        context.realTimeProfit += profitDiff
        context.stockRealTimeProfit += profitDiff
        # TODO: Record

    def closeFuture(self, direction: str, symbol: str, price: float, vol: int, reason: str):
        """
        期货平仓
        """
        profit = 0.0  # 平仓盈亏
        settleProfit = 0.0  # 盯市盈亏
        profitDiff = 0.0  # 相对于上一个K线的额外盈亏 -> 计入realTimeProfit
        margin = 0.0
        context = Context.get_instance()
        if direction == "long":
            if symbol not in context.futureLongPosition:
                print(f"没有该期货多头的持仓:{symbol}")
                return
            pos_list: List[FuturePosition] = context.futureLongPosition[symbol]
        else:
            if symbol not in context.stockShortPosition:
                print(f"没有该期货空头的持仓:{symbol}")
                return
            pos_list: List[FuturePosition] = context.futureShortPosition[symbol]

        sign_list = []
        current_vol_list = []
        ori_price_list = []
        pre_price_list = []
        pre_margin_list = []
        pre_settle_list = []
        time_monitor_list = []
        hold_days_list = []
        for pos in pos_list:
            sign_list.append(pos.sign)
            current_vol_list.append(pos.vol)
            ori_price_list.append(pos.ori_price)
            pre_price_list.append(pos.pre_price)
            pre_settle_list.append(pos.pre_settle)
            pre_margin_list.append(pos.margin)
            time_monitor_list.append(pos.time_monitor)
            hold_days_list.append(pos.hold_days)

        # 获取允许平仓的最大数量
        state = True
        if -2 in time_monitor_list:
            state = False
            index = time_monitor_list.index(-2)
            current_vol = sum(current_vol_list[:index])
        else:
            current_vol = sum(current_vol_list)
        # 获取平仓的最终数量
        max_vol = min(current_vol, vol)
        record_vol = max_vol  # for record
        if max_vol >= current_vol and state:  # 全部平仓
            for i in range(0, len(pos_list)):
                posVol = current_vol_list[i]
                oriPrice = ori_price_list[i]
                prePrice = pre_price_list[i]
                preMargin = pre_margin_list[i]
                holdDays = hold_days_list[i]
                preSettle = pre_settle_list[i]
                profit += (price - posPrice) * posVol * posSign  # 平仓盈亏
                if holdDays == 0:  # TODO: 日内平仓,需要添加对应的逻辑
                    settleProfit += (price - oriPrice) * posVol * posSign
                    profitDiff += (price - prePrice) * posVol * posSign
                else:
                    settleProfit += (price - preSettle) * posVol * posSign
                    profitDiff += (price - prePrice) * posVol * posSign
                margin += preMargin  # (preMargin + settleProfit) # 这里保证金是实时更新的
            # 再对持仓&持仓视图进行批处理
            if direction == "long":
                del context.stockLongSummary[symbol]  # 直接删除该标的的持仓视图
                del context.stockLongPosition[symbol]  # 直接删除该标的的持仓
            else:
                del context.stockShortSummary[symbol]
                del context.stockShortPosition[symbol]

        else:  # 部分平仓
            # 先对视图进行批处理
            if direction == "long":
                context.futureLongSummary[symbol].closeUpdate(price, max_vol)
            else:
                context.futureShortSummary[symbol].closeUpdate(price, max_vol)
            for i in range(0, len(pos_list)):
                posVol = current_vol_list[i]
                oriPrice = ori_price_list[i]
                preMargin = pre_margin_list[i]
                preSettle = pre_settle_list[i]
                holdDays = hold_days_list[i]
                posSign = sign_list[i]
                if max_vol >= posVol:  # 当前仓位能够全部平仓
                    profit += (price - oriPrice) * posVol * posSign
                    if holdDays == 0:  # TODO: 日内平仓,需要添加对应的逻辑
                        settleProfit += (price - oriPrice) * posVol * posSign
                        profitDiff += (price - prePrice) * posVol * posSign
                    else:
                        settleProfit += (price - preSettle) * posVol * posSign
                        profitDiff += (price - prePrice) * posVol * posSign
                    margin += preMargin  # (preMargin + settleProfit)    # 这里margin是随着行情更新而更新的
                    pos_list.pop(0)
                    max_vol -= posVol
                else:  # 当前仓位部分平仓
                    pos_list[0].vol -= max_vol
                    profit += (price - oriPrice) * max_vol * posSign
                    if holdDays == 0:  # TODO: 日内平仓,需要添加对应的逻辑
                        settleProfit += (price - oriPrice) * max_vol * posSign
                        profitDiff += (price - prePrice) * max_vol * posSign
                    else:
                        settleProfit += (price - preSettle) * max_vol * posSign
                        profitDiff += (price - prePrice) * max_vol * posSign
                    margin += preMargin * (max_vol / posVol)
                    break
        # 结算
        context.cash += (margin + profitDiff)  # 收回的100%保证金
        context.futureCash += margin
        context.profit += profit
        context.futureProfit += profit
        context.futureSettleProfit += settleProfit
        context.realTimeProfit += profitDiff
        context.futureRealTimeProfit += profitDiff
        # TODO: Record

    def monitorStockPosition(self, direction: str, sequence: bool):
        """
        【柜台处理订单后运行,可重复运行】每日盘中运行,负责监控当前持仓是否满足限制平仓要求
        sequence=true 假设high先到来
        sequence=false 假设low先到来
        :param sequence: bool
        :return:
        """
        # 获取当前回测上下文配置
        context = Context.get_instance()
        if direction == "long":
            totalPos: List[StockPosition] = context.stockLongPosition
        else:
            totalPos: List[StockPosition] = context.stockShortPosition
        if len(pos) == 0:
            return

        dataDict = DataDict.get_instance()
        day = context.current_date
        minute = context.current_minute
        timestamp = context.current_timestamp
        if minute not in dataDict.stockKDict:
            return
        barDict = dataDict.stockKDict[minute]
        infoDict: Dict[str, StockInfo] = dataDict.stockInfoDict

        for symbol in totalPos:
            info = infoDict[symbol]
            bar = barDict[symbol]

            # 基本信息
            end_date = info.end_date
            high_price = bar.high
            low_price = bar.low
            close_price = bar.close
            pos_list = totalPos[symbol]
            i: int = 0
            while i < len(pos_list):    # 过程中可能会平仓
                if symbol not in totalPos:
                    i+=1
                    continue
                pos = pos_list[i]
                time_monitor = pos.time_monitor
                static_monitor = pos.static_monitor
                dynamic_monitor = pos.dynamic_monitor
                if time_monitor < 0:    # -2:<最短持仓时间/ -1:属于最短持仓~最长持仓时间之间的仓位
                    i+=1
                    continue
                i+=1

                # 获取持仓信息
                posVol = pos.vol
                max_timestamp = pos.max_timestamp

                # 时间维度平仓判断[在PyBackTest中，时间维度优先级>价格维度]
                if time_monitor == 1:
                    if day >= end_date:
                        self.closeStock(direction=direction, symbol=symbol, vol=posVol,
                                         price=close_price, reason="到期平仓")
                        continue
                    if timestamp > max_timestamp:   # 超过最长持仓时间
                        self.closeStock(direction=direction, symbol=symbol, vol=posVol,
                                         price=close_price, reason="最长持仓时间")
                        continue

                # 静态限价单平仓判断
                static_high = pos.static_high
                static_low = pos.static_low
                if static_monitor == 1:
                    if sequence: # 假设最高价先到来
                        if static_high and high_price >= static_high:
                            self.closeStock(direction, symbol=symbol, price=close_price, vol=posVol,
                                             reason="静态最高价")
                            continue
                        if static_low and low_price <= static_low:
                            self.closeStock(direction, symbol=symbol, price=close_price, vol=posVol,
                                             reason="静态最低价")
                            continue
                    else:   # 假设最低价先到来
                        if static_low and low_price <= static_low:
                            self.closeStock(direction, symbol=symbol, price=close_price, vol=posVol,
                                             reason="静态最低价")
                            continue
                        if static_high and high_price >= static_high:
                            self.closeStock(direction, symbol=symbol, price=close_price, vol=posVol,
                                             reason="静态最高价")
                            continue

                # 动态限价单平仓判断
                dynamic_high = pos.dynamic_high
                dynamic_low = pos.dynamic_low
                if dynamic_monitor == 1:
                    if sequence:
                        if dynamic_high and high_price >= dynamic_high:
                            self.closeStock(direction, symbol=symbol, vol=posVol, price=close_price,
                                             reason="动态最高价")
                            continue
                        if dynamic_low and low_price <= dynamic_low:
                            self.closeStock(direction, symbol=symbol, vol=posVol, price=close_price,
                                             reason="动态最低价")
                            continue
                    else:
                        if dynamic_low and low_price <= dynamic_low:
                            self.closeStock(direction, symbol=symbol, vol=posVol, price=close_price,
                                             reason="动态最低价")
                            continue
                        if dynamic_high and high_price >= dynamic_high:
                            self.closeStock(direction, symbol=symbol, vol=posVol, price=close_price,
                                             reason="动态最高价")
                            continue

    def monitorFuturePosition(self, direction: str, sequence: bool):
        """
        【柜台处理订单后运行,可重复运行】每日盘中运行,负责监控当前持仓是否满足限制平仓要求
        sequence=true 假设high先到来
        sequence=false 假设low先到来
        :param direction:
        :param sequence:
        :return:
        """
        # 获取当前回测上下文配置
        context = Context.get_instance()
        if direction == "long":
            totalPos: List[FuturePosition] = context.futureLongPosition
        else:
            totalPos: List[FuturePosition] = context.futureShortPosition
        if len(pos) == 0:
            return

        dataDict = DataDict.get_instance()
        day = context.current_date
        minute = context.current_minute
        timestamp = context.current_timestamp
        if minute not in dataDict.futureKDict:
            return
        barDict = dataDict.futureKDict[minute]
        infoDict: Dict[str, FutureInfo] = dataDict.futureInfoDict

        for symbol in totalPos:
            info = infoDict[symbol]
            bar = barDict[symbol]

            # 基本信息
            end_date = info.end_date
            high_price = bar.high
            low_price = bar.low
            close_price = bar.close
            pos_list = totalPos[symbol]
            i: int = 0
            while i < len(pos_list):    # 过程中可能会平仓
                if symbol not in totalPos:
                    i+=1
                    continue
                pos = pos_list[i]
                time_monitor = pos.time_monitor
                static_monitor = pos.static_monitor
                dynamic_monitor = pos.dynamic_monitor
                if time_monitor < 0:    # -2:<最短持仓时间/ -1:属于最短持仓~最长持仓时间之间的仓位
                    i+=1
                    continue
                i+=1

                # 获取持仓信息
                posVol = pos.vol
                max_timestamp = pos.max_timestamp

                # 时间维度平仓判断[在PyBackTest中，时间维度优先级>价格维度]
                if time_monitor == 1:
                    if day >= end_date:
                        self.closeFuture(direction=direction, symbol=symbol, vol=posVol,
                                         price=close_price, reason="到期平仓")
                        continue
                    if timestamp > max_timestamp:   # 超过最长持仓时间
                        self.closeFuture(direction=direction, symbol=symbol, vol=posVol,
                                         price=close_price, reason="最长持仓时间")
                        continue

                # 静态限价单平仓判断
                static_high = pos.static_high
                static_low = pos.static_low
                if static_monitor == 1:
                    if sequence: # 假设最高价先到来
                        if static_high and high_price >= static_high:
                            self.closeFuture(direction, symbol=symbol, price=close_price, vol=posVol,
                                             reason="静态最高价")
                            continue
                        if static_low and low_price <= static_low:
                            self.closeFuture(direction, symbol=symbol, price=close_price, vol=posVol,
                                             reason="静态最低价")
                            continue
                    else:   # 假设最低价先到来
                        if static_low and low_price <= static_low:
                            self.closeFuture(direction, symbol=symbol, price=close_price, vol=posVol,
                                             reason="静态最低价")
                            continue
                        if static_high and high_price >= static_high:
                            self.closeFuture(direction, symbol=symbol, price=close_price, vol=posVol,
                                             reason="静态最高价")
                            continue

                # 动态限价单平仓判断
                dynamic_high = pos.dynamic_high
                dynamic_low = pos.dynamic_low
                if dynamic_monitor == 1:
                    if sequence:
                        if dynamic_high and high_price >= dynamic_high:
                            self.closeFuture(direction, symbol=symbol, vol=posVol, price=close_price,
                                             reason="动态最高价")
                            continue
                        if dynamic_low and low_price <= dynamic_low:
                            self.closeFuture(direction, symbol=symbol, vol=posVol, price=close_price,
                                             reason="动态最低价")
                            continue
                    else:
                        if dynamic_low and low_price <= dynamic_low:
                            self.closeFuture(direction, symbol=symbol, vol=posVol, price=close_price,
                                             reason="动态最低价")
                            continue
                        if dynamic_high and high_price >= dynamic_high:
                            self.closeFuture(direction, symbol=symbol, vol=posVol, price=close_price,
                                             reason="动态最高价")
                            continue
