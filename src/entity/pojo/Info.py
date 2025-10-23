import pandas as pd

class Info:
    def __init__(self, trade_date: pd.Timestamp, symbol: str,
                 open_price: float, high_price: float, low_price: float,
                 close_price: float, start_date: pd.Timestamp, end_date: pd.Timestamp):
        self.trade_date = trade_date
        self.symbol = symbol
        self.open_price = open_price
        self.high_price = high_price
        self.low_price = low_price
        self.close_price = close_price
        self.start_date = start_date
        self.end_date = end_date

class StockInfo(Info):
    def __init__(self, trade_date: pd.Timestamp, symbol: str,
                 open_price: float, high_price: float, low_price: float,
                 close_price: float, start_date: pd.Timestamp, end_date: pd.Timestamp):
        super().__init__(trade_date, symbol, open_price, high_price, low_price,
                         close_price, start_date, end_date)

class FutureInfo(Info):
    def __init__(self, trade_date: pd.Timestamp, symbol: str,
                 open_price: float, high_price: float, low_price: float,
                 pre_settle: float, settle: float, margin_rate: float,
                 close_price: float, start_date: pd.Timestamp, end_date: pd.Timestamp):
        super().__init__(trade_date, symbol, open_price, high_price, low_price,
                         close_price, start_date, end_date)
        self.pre_settle = pre_settle
        self.settle = settle
        self.margin_rate = margin_rate
