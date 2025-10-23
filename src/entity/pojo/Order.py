import pandas as pd

class Order:
    def __init__(self, order_type: str, symbol: str, vol: int, price: float,
                 create_timestamp: pd.Timestamp, min_order_timestamp: pd.Timestamp,
                 max_order_timestamp: pd.Timestamp, reason: str):
        self.order_type = order_type
        self.symbol = symbol
        self.vol = vol
        self.price = price
        self.create_timestamp = create_timestamp
        self.min_order_timestamp = min_order_timestamp
        self.max_order_timestamp = max_order_timestamp
        self.reason = reason

class StockOrder(Order):
    def __init__(self, direction: str, order_type: str, symbol: str, vol: int, price: float,
                 create_timestamp: pd.Timestamp, min_order_timestamp: pd.Timestamp,
                 max_order_timestamp: pd.Timestamp, reason: str):
        super().__init__(order_type, symbol, vol, price, create_timestamp, min_order_timestamp, max_order_timestamp, reason)
        self.partialOrder = False # 默认当前订单为完整订单
        self.order_direction = direction
        self.static_profit = 0.0
        self.static_loss = 0.0
        self.dynamic_profit = 0.0
        self.dynamic_loss = 0.0

class FutureOrder(Order):
    def __init__(self, direction: str, symbol: str, vol: int, price: float,
                 create_timestamp: pd.Timestamp, min_order_timestamp: pd.Timestamp,
                 max_order_timestamp: pd.Timestamp, reason: str):
        super().__init__(symbol, vol, price, create_timestamp, min_timestamp, max_timestamp, min_order_timestamp, max_order_timestamp, reason)
        self.order_direction = direction
        self.partialOrder = False   # 默认当前订单为完整订单

class StockOpenOrder(StockOrder):
    def __init__(self, direction: str, symbol: str, vol: int, price: float,
                 create_timestamp: pd.Timestamp,
                 min_timestamp: pd.Timestamp,
                 max_timestamp: pd.Timestamp,
                 min_order_timestamp: pd.Timestamp,
                 max_order_timestamp: pd.Timestamp,
                 static_profit: float, static_loss: float, dynamic_profit: float,
                 dynamic_loss: float, commission: float, reason: str, partialOrder: bool):
        super().__init__(direction, symbol, vol, price, create_timestamp, min_order_timestamp, max_order_timestamp, reason)
        self.order_type = "open"
        self.partialOrder = partialOrder
        self.min_timestamp = min_timestamp
        self.max_timestamp = max_timestamp
        self.min_order_timestamp = min_order_timestamp
        self.max_order_timestamp = max_order_timestamp
        self.static_profit = static_profit
        self.static_loss = static_loss
        self.dynamic_profit = dynamic_profit
        self.dynamic_loss = dynamic_loss
        self.commission = commission

class FutureOpenOrder(FutureOrder):
    def __init__(self, direction: str, symbol: str, vol: int, price: float,
                 create_timestamp: pd.Timestamp,
                 min_timestamp: pd.Timestamp,
                 max_timestamp: pd.Timestamp,
                 min_order_timestamp: pd.Timestamp,
                 max_order_timestamp: pd.Timestamp,
                 static_profit: float, static_loss: float, dynamic_profit: float,
                 dynamic_loss: float, commission: float, reason: str, partialOrder: bool):
        super().__init__(direction, symbol, vol, price, create_timestamp, min_order_timestamp, max_order_timestamp, reason)
        self.order_type = "open"
        self.partialOrder = partialOrder
        self.min_timestamp = min_timestamp
        self.max_timestamp = max_timestamp
        self.min_order_timestamp = min_order_timestamp
        self.max_order_timestamp = max_order_timestamp
        self.static_profit = static_profit
        self.static_loss = static_loss
        self.dynamic_profit = dynamic_profit
        self.dynamic_loss = dynamic_loss
        self.commission = commission

class StockCloseOrder(StockOrder):
    def __init__(self, direction: str, symbol: str, vol: int, price: float,
                 create_timestamp: pd.Timestamp, min_order_timestamp: pd.Timestamp,
                 max_order_timestamp: pd.Timestamp, reason: str, partialOrder: bool):
        super().__init__(direction, symbol, vol, price, create_timestamp, min_order_timestamp, max_order_timestamp, reason)
        self.order_type = "close"
        self.partialOrder = partialOrder


class FutureCloseOrder(FutureOrder):
    def __init__(self, direction: str, symbol: str, vol: int, price: float,
                 create_timestamp: pd.Timestamp, min_order_timestamp: pd.Timestamp,
                 max_order_timestamp: pd.Timestamp, reason: str, partialOrder: bool):
        super().__init__(direction, symbol, vol, price, create_timestamp, min_order_timestamp, max_order_timestamp, reason)
        self.order_type = "close"
        self.partialOrder = partialOrder
