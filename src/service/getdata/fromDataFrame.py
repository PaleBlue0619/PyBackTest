import pandas as pd
from typing import Dict,List
from src.entity.pojo.Info import StockInfo,FutureInfo

class fromDataFrame:    # 从DataFrame -> 回测需要的对象/字典/对象字典格式
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.dataCols = data.columns.tolist()

    def toStockInfo(self, dateCol: str, symbolCol: str,
                  openCol: str, highCol: str, lowCol: str, closeCol: str,
                  startDateCol: str = None, endDateCol: str = None) -> Dict[str, StockInfo]:
        """
        stockInfo: InfoDict<String, StockInfo>>
        """
        stockInfo = {}
        for index, row in self.data.iterrows():
            tradeDate = pd.Timestamp(row[dateCol])
            symbol = row[symbolCol]
            open_price = row[openCol]
            high_price = row[highCol]
            low_price = row[lowCol]
            close_price = row[closeCol]
            start_date = pd.Timestamp(row[startDateCol])
            end_date = pd.Timestamp(row[endDateCol])
            stockInfo[symbol] = StockInfo(tradeDate, symbol, open_price, high_price, low_price, close_price, start_date, end_date)
        return stockInfo

    def toStockBar(self, isMinBar: bool, dateCol:  str, symbolCol: str,
                  openCol: str, highCol: str, lowCol: str, closeCol: str, volumeCol: str, minuteCol: str = None) -> Dict[pd.Timestamp, Dict[str, dict]]:
        """
        stockBar: TreeMap<LocalTime, Map<String, Bar>> -> Bar: {"open": "high": "low": "close":}
        :return:
        """
        stockBar = {}
        for index, row in self.data.iterrows():
            tradeDate = pd.Timestamp(row[dateCol])
            if isMinBar:
                tradeTime = pd.Timestamp(row[minuteCol])
            else:
                tradeTime = pd.Timestamp(tradeDate.strftime("%Y%m%d")+" 15:00:00.000")
            symbol = row[symbolCol]
            open_price = row[openCol]
            high_price = row[highCol]
            low_price = row[lowCol]
            close_price = row[closeCol]
            volume = row[volumeCol]
            if tradeTime not in stockBar:
                stockBar[tradeTime] = {}
            stockBar[tradeTime][symbol] = {"open": open_price, "high": high_price, "low": low_price, "close": close_price, "volume": volume}
        return stockBar