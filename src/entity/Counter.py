import pandas as pd
from src.entity.Context import Context
from src.entity.DataDict import DataDict
from src.entity.CounterBehavior import CounterBehavior

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
                print("OrderNum:"+order_id+"Behavior:"+order_type+"Direction:"+direction+"symbol:"+symbol+"price:"+str(price)+"vol:"+str(vol)+"failed[Out of Timestamp]");
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
                print("OrderNum:"+order_id+"Behavior:"+order_type+"Direction:"+direction+"symbol:"+symbol+"price:"+str(price)+"vol:"+str(vol)+"failed[Out of Timestamp]");
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