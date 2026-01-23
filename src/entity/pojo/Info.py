import pandas as pd
"""
由于Python的反序列化性能太过糟糕 -> 仍然采用字典进行存储每一行的数据
StockInfo: {"trade_date", "symbol", "open_price", "high_price", "low_price", "close_price", "start_date", "end_date"}
FutureInfo: {"trade_date", "symbol", "open_price", "high_price", "low_price", "close_price", "margin_rate", "pre_settle", "settle", "start_date", "end_date"}
"""
