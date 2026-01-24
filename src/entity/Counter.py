import pandas as pd
from src.entity.pojo.Position import StockPosition,FuturePosition
from src.entity.pojo.Summary import StockSummary,FutureSummary
from src.entity.Context import Context
from src.entity.DataDict import DataDict
from src.entity.CounterBehavior import CounterBehavior
from src.entity.pojo.Statistics import Statistics
from src.entity.pojo.TradeDetails import TradeDetails
from src.entity.pojo.OrderDetails import OrderDetails
from typing import List, Dict

class Counter(CounterBehavior):
    def __init__(self):
        super(Counter, self).__init__()

    @staticmethod
    def processStockOrder(open_threshold: float, close_threshold: float):
        """
        自定义订单撮合函数
        :param open_threshold:   当前开仓最多只能成交这根K线成交量的open_threshold倍
        :param close_threshold:   当前平仓最多只能成交这根K线成交量的close_threshold倍
        :return:
        """

        # 获取当前配置实例
        context = Context.get_instance()
        dataDict = DataDict.get_instance()
        minute = context.current_minute
        timestamp = context.current_timestamp
        stockCounter = context.stockCounter

        if minute not in dataDict.stockKDict:
            return
        barDict = dataDict.stockKDict[minute]

        # 记录需要删除的order_id
        delete_ids = []
        for order_id, order in stockCounter.items():
            # 获取当前订单对象的属性值
            order_type = order.order_type   # open/close
            direction = order.order_direction   # long/short
            symbol = order.symbol
            price = order.price
            vol = order.vol
            min_order_timestamp = order.min_order_timestamp
            max_order_timestamp = order.max_order_timestamp
            partialOrder = order.partialOrder
            if max_order_timestamp <= timestamp:    # 订单已过期
                delete_ids.append(order_id)
                print("OrderNum:"+str(order_id)+"Behavior:"+str(order_type)+"Direction:"+str(direction)+"symbol:"+str(symbol)+"price:"+str(price)+"vol:"+str(vol)+"failed[Out of Timestamp]");
            elif timestamp >= min_order_timestamp:
                if symbol not in barDict:
                    continue
                bar = barDict[symbol]
                low = bar["low"]
                high = bar["high"]
                close = bar["close"]
                volume = bar["volume"]
                if low and high and close and volume:
                    if partialOrder: # 说明是部分成交的订单
                        price = close
                    if low<=price<=high:
                        # 开仓订单
                        if order_type == "open":
                            openVolThreshold = int(volume * open_threshold)
                            if vol<=openVolThreshold:   # 完全成交
                                delete_ids.append(order_id)
                            else:   # 部分成交
                                order.partialOrder = True
                                order.vol -= openVolThreshold
                                vol = openVolThreshold
                            if vol >= 1.0:
                                Counter.openStock(direction=direction, symbol=symbol, vol=vol, price=price,
                                               static_profit=order.static_profit, static_loss=order.static_loss,
                                               dynamic_profit=order.dynamic_profit, dynamic_loss=order.dynamic_loss,
                                               min_timestamp=order.min_timestamp, max_timestamp=order.max_timestamp,
                                               reason=order.reason)
                        # 平仓订单
                        else:
                            closeVolThreshold = int(volume * close_threshold)
                            if vol<=closeVolThreshold:  # 完全成交
                                delete_ids.append(order_id)
                            else:   # 部分成交
                                order.partialOrder = True
                                order.vol -= closeVolThreshold
                                vol = closeVolThreshold
                            if vol >= 1.0:
                                Counter.closeStock(direction=direction, symbol=symbol, vol=vol, price=price,
                                                reason=order.reason)

        # 删除柜台已经完全成交的订单
        for order_id in delete_ids:
            stockCounter.pop(order_id)

    @staticmethod
    def processFutureOrder(open_threshold: float, close_threshold: float):
        """
        自定义订单撮合函数
        :param open_threshold:   当前开仓最多只能成交这根K线成交量的open_threshold倍
        :param close_threshold:   当前平仓最多只能成交这根K线成交量的close_threshold倍
        :return:
        """

        # 获取当前配置实例
        context = Context.get_instance()
        dataDict = DataDict.get_instance()
        minute = context.current_minute
        timestamp = context.current_timestamp
        futureCounter = context.futureCounter

        if minute not in dataDict.futureKDict:
            return
        barDict = dataDict.futureKDict[minute]

        # 记录需要删除的order_id
        delete_ids = []
        for order_id, order in futureCounter.items():
            # 获取当前订单对象的属性值
            order_type = order.order_type   # open/close
            direction = order.order_direction   # long/short
            symbol = order.symbol
            price = order.price
            vol = order.vol
            min_order_timestamp = order.min_order_timestamp
            max_order_timestamp = order.max_order_timestamp
            partialOrder = order.partialOrder
            if max_order_timestamp <= timestamp:    # 订单已过期
                delete_ids.append(order_id)
                print("OrderNum:"+str(order_id)+"Behavior:"+str(order_type)+"Direction:"+str(direction)+"symbol:"+str(symbol)+"price:"+str(price)+"vol:"+str(vol)+"failed[Out of Timestamp]");
            elif timestamp >= min_order_timestamp:
                if symbol not in barDict:
                    continue
                bar = barDict[symbol]
                low = bar["low"]
                high = bar["high"]
                close = bar["close"]
                volume = bar["volume"]
                if low and high and close and volume:
                    if partialOrder: # 说明是部分成交的订单
                        price = close
                    if low<=price<=high:
                        # 开仓订单
                        if order_type == "open":
                            openVolThreshold = int(volume * open_threshold)
                            if vol<=openVolThreshold:   # 完全成交
                                delete_ids.append(order_id)
                            else:   # 部分成交
                                order.partialOrder = True
                                order.vol -= openVolThreshold
                                vol = openVolThreshold
                            if vol >= 1.0:
                                Counter.openFuture(direction=direction, symbol=symbol, vol=vol, price=price,
                                               static_profit=order.static_profit, static_loss=order.static_loss,
                                               dynamic_profit=order.dynamic_profit, dynamic_loss=order.dynamic_loss,
                                               min_timestamp=order.min_timestamp, max_timestamp=order.max_timestamp,
                                               reason=order.reason)
                        # 平仓订单
                        else:
                            closeVolThreshold = int(volume * close_threshold)
                            if vol<=closeVolThreshold:  # 完全成交
                                delete_ids.append(order_id)
                            else:   # 部分成交
                                order.partialOrder = True
                                order.vol -= closeVolThreshold
                                vol = closeVolThreshold
                            if vol >= 1.0:
                                Counter.closeFuture(direction=direction, symbol=symbol, vol=vol, price=price,
                                                reason=order.reason)
        # 删除柜台已经完全成交的订单
        for order_id in delete_ids:
            futureCounter.pop(order_id)

    @staticmethod
    def getAvailableCash(assetType: str = None) -> float:
        context = Context.get_instance()
        if assetType == "stock":
            return context.stockCash
        if assetType == "future":
            return context.futureCash
        return context.cash

    @staticmethod
    def getTradeStatistics(statsType: str):
        """
        :param statsType: Optional {"cash","stockCash","futureCash",
                                    "profit","stockProfit","futureProfit"
                                    "realTimeProfit","stockRealTimeProfit","futureRealTimeProfit"
                                    }
        :return: 统计指标
        """
        # 获取统计实例对象
        statistics = Statistics.get_instance()
        if statsType == "cash":
            return statistics.cashDict
        if statsType == "stockCash":
            return statistics.stockCashDict
        if statsType == "futureCash":
            return statistics.futureCashDict
        if statsType == "profit":
            return statistics.profitDict
        if statsType == "stockProfit":
            return statistics.stockProfitDict
        if statsType == "futureProfit":
            return statistics.futureProfitDict
        if statsType == "realTimeProfit":
            return statistics.realTimeProfitDict
        if statsType == "stockRealTimeProfit":
            return statistics.stockRealTimeProfitDict
        if statsType == "futureRealTimeProfit":
            return statistics.futureRealTimeProfitDict
        return pd.DataFrame(
            {
                "TradeDate": statistics.cashDict.keys(),
                "cash": statistics.cashDict.values(),
                "stockCash": statistics.stockCashDict.values(),
                "futureCash": statistics.futureCashDict.values(),
                "profit": statistics.profitDict.values(),
                "stockProfit": statistics.stockProfitDict.values(),
                "futureProfit": statistics.futureProfitDict.values(),
                "realTimeProfit": statistics.realTimeProfitDict.values(),
                "stockRealTimeProfit": statistics.stockRealTimeProfitDict.values(),
                "futureRealTimeProfit": statistics.futureRealTimeProfitDict.values()
            }
        )

    @staticmethod
    def getOrderDetails(assetType: str) -> pd.DataFrame:
        """
        返回DataFrame -> orderNum为第一列
        :param assetType:
        :return:
        """
        # 获取当前实例
        orderDetails = OrderDetails.get_instance()
        if assetType == "stock":
            df = pd.DataFrame.from_dict(orderDetails.stockRecord, orient='index')
        elif assetType == "future":
            df = pd.DataFrame.from_dict(orderDetails.futureRecord, orient='index')
        df.insert(0, 'orderNum', df.index)
        df.reset_index(drop=True, inplace=True)
        return df

    @staticmethod
    def getTradeDetails(assetType: str) -> pd.DataFrame:
        """
        返回DataFrame -> tradeNum为第一列
        :param assetType:
        :return:
        """
        # 获取当前实例
        tradeDetails = TradeDetails.get_instance()
        if assetType == "stock":
            df = pd.DataFrame.from_dict(tradeDetails.stockRecord, orient='index')
        elif assetType == "future":
            df = pd.DataFrame.from_dict(tradeDetails.futureRecord, orient='index')
        df.insert(0, 'tradeNum', df.index)
        df.reset_index(drop=True, inplace=True)
        return df

    @staticmethod
    def getStockPosition(direction: str, symbol: List[str] = None) -> Dict[str, List[StockPosition]]:
        """
        :param direction: 股票持仓方向: long/short
        :param symbol: 代码: 000001.SZ/ -> None表示所有持仓
        :return:
        """
        # 获取当前配置实例
        context = Context.get_instance()
        if direction == "long":
            if symbol is None:
                return context.stockLongPosition
            else:
                return {s: context.stockLongPosition[s] for s in symbol if s in context.stockLongPosition}
        if direction == "short":
            if symbol is None:
                return context.stockShortPosition
            else:
                return {s: context.stockShortPosition[s] for s in symbol if s in context.stockShortPosition}

    @staticmethod
    def getFuturePosition(direction: str, symbol: List[str] = None) -> Dict[str, List[FuturePosition]]:
        """
        :param direction: 期货持仓方向: long/short
        :param symbol: 代码: A0001/ -> None表示所有持仓
        :return:
        """
        # 获取当前配置实例
        context = Context.get_instance()
        if direction == "long":
            if symbol is None:
                return context.futureLongPosition
            else:
                if symbol in context.futureLongPosition:
                    return context.futureLongPosition[symbol]
        if direciton == "short":
            if symbol is None:
                return context.futureShortPosition
            else:
                if symbol in context.futureShortPosition:
                    return context.futureShortPosition[symbol]

    @staticmethod
    def getStockSummary(direction: str, symbol: List[str] = None) -> Dict[str, StockSummary]:
        """
        :param direction: 股票持仓方向: long/short
        :param symbol: 代码: A0001/ -> None表示所有持仓
        :return:
        """
        # 获取当前配置实例
        context = Context.get_instance()
        if direction == "long":
            if symbol is None:
                return context.stockLongSummary
            else:
                return {s: context.stockLongSummary[s] for s in symbol if s in context.stockLongSummary}
        if direction == "short":
            if symbol is None:
                return context.stockShortSummary
            else:
                return {s: context.stockShortSummary[s] for s in symbol if s in context.stockShortSummary}

    @staticmethod
    def getFutureSummary(direction: str, symbol: List[str] = None) -> Dict[str, FutureSummary]:
        """
        :param direction: 期货持仓方向: long/short
        :param symbol: 代码: A0001/ -> None表示所有持仓
        :return:
        """
        # 获取当前配置实例
        context = Context.get_instance()
        if direction == "long":
            if symbol is None:
                return context.futureLongSummary
            else:
                return {s: context.futureLongSummary[s] for s in symbol if s in context.futureLongSummary}
        if direction == "short":
            if symbol is None:
                return context.futureShortSummary
            else:
                return {s: context.futureShortSummary[s] for s in symbol if s in context.futureShortSummary}
