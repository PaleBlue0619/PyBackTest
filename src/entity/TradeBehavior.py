import pandas as pd
from pojo.Order import *
from Context import Context

class TradeBehavior:
    @staticmethod
    def orderOpenStock(direction: str, symbol: str, vol: int, price: double,
                       static_profit: float, static_loss: float,
                       dynamic_profit: float, dynamic_loss: float,
                       min_timestamp: float, max_timestamp: float,
                       min_order_timestamp: float, max_order_timestamp: float,
                       commission: float, reason: float, partial_order: bool):
        # 获取配置实例
        context = Context.get_instance()
        orderNum = context.get_nextOrderNum()   # 获取自增订单编号

        min_timestamp = config.start_date if not min_timestamp else min_timestamp
        max_timestamp = config.end_date if not max_timestamp else max_timestamp
        min_order_timestamp = context.start_time_stamp if not min_order_timestamp else min_order_timestamp
        max_order_timestamp = context.end_time_stamp if not max_order_timestamp else max_order_timestamp

        # 创建订单对象
        order = StockOpenOrder(direction=direction,
            symbol=symbol, vol=vol, price=price, create_timestamp=context.current_timestamp,
            min_timestamp=min_timestamp, max_timestamp=max_timestamp,
            min_order_timestamp=min_order_timestamp, max_order_timestamp=max_order_timestamp,
            static_profit=static_profit, static_loss=static_loss,
            dynamic_profit=dynamic_profit, dynamic_loss=dynamic_loss,
            commission=commission, reason=reason, partialOrder=partial_order
        )
        # 将订单添加到柜台
        context.stockCounter[orderNum] = order
        # TODO: 添加到记录中

    @staticmethod
    def orderCloseStock(direction: str, symbol: str, vol: int, price: float,
                        min_order_timestamp: pd.Timestamp, max_order_timestamp: pd.Timestamp,
                        reason: str, partial_order: bool):
        # 获取配置实例
        context = Context.get_instance()
        orderNum = context.get_nextOrderNum()

        min_order_timestamp = context.start_date if not min_order_timestamp else min_order_timestamp
        max_order_timestamp = context.end_date if not max_order_timestamp else max_order_timestamp

        order = StockCloseOrder(
            direction=direction,
            symbol=symbol,
            vol=vol,
            price=price,
            create_timestamp=context.current_timestamp,
            min_order_timestamp=min_order_timestamp,
            max_order_timestamp=max_order_timestamp,
            reason=reason,
            partialOrder=partial_order
        )
        # 将订单添加到柜台
        context.stockCounter[orderNum] = order
        # TODO: 添加到记录中


    @staticmethod
    def orderOpenFuture(direction: str, symbol: str, vol: int, price: float,
                        static_profit: float, static_loss: float,
                        dynamic_profit: float, dynamic_loss: float,
                        min_timestamp: float, max_timestamp: float,
                        min_order_timestamp: float, max_order_timestamp: float,
                        commission: float, reason: float, partial_order: bool
                        ):
        # 获取配置实例
        context = Context.get_instance()
        orderNum = context.get_nextOrderNum()

        min_timestamp = config.start_date if not min_timestamp else min_timestamp
        max_timestamp = config.end_date if not max_timestamp else max_timestamp
        min_order_timestamp = context.start_time_stamp if not min_order_timestamp else min_order_timestamp
        max_order_timestamp = context.end_time_stamp if not max_order_timestamp else max_order_timestamp

        # 创建订单对象
        order = FutureOpenOrder(direction=direction,
                               symbol=symbol, vol=vol, price=price, create_timestamp=context.current_timestamp,
                               min_timestamp=min_timestamp, max_timestamp=max_timestamp,
                               min_order_timestamp=min_order_timestamp, max_order_timestamp=max_order_timestamp,
                               static_profit=static_profit, static_loss=static_loss,
                               dynamic_profit=dynamic_profit, dynamic_loss=dynamic_loss,
                               commission=commission, reason=reason, partialOrder=partial_order
                               )
        # 将订单添加到柜台
        context.futureCounter[orderNum] = order
        # TODO: 添加到记录中

    def orderCloseFuture(self, direction: str, symbol: str, vol: int, price: float,
                         min_order_timestamp: pd.Timestamp, max_order_timestamp: pd.Timestamp,
                         reason: str, partial_order: bool):
        # 获取配置实例
        context = Context.get_instance()
        orderNum = context.get_nextOrderNum()

        min_order_timestamp = context.start_date if not min_order_timestamp else min_order_timestamp
        max_order_timestamp = context.end_date if not max_order_timestamp else max_order_timestamp

        order = FutureCloseOrder(
            direction=direction,
            symbol=symbol,
            vol=vol,
            price=price,
            create_timestamp=context.current_timestamp,
            min_order_timestamp=min_order_timestamp,
            max_order_timestamp=max_order_timestamp,
            reason=reason,
            partialOrder=partial_order
        )
        # 将订单添加到柜台
        context.futureCounter[orderNum] = order
        # TODO: 添加到记录中