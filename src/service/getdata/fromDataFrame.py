import pandas as pd
from typing import Dict,List
from src.entity.pojo.Info import StockInfo,FutureInfo
from joblib import Parallel, delayed    # 多进程
from concurrent.futures import ThreadPoolExecutor   # 多线程
from concurrent.futures import as_completed
from functools import partial

class fromDataFrame:    # 从DataFrame -> 回测需要的对象/字典/对象字典格式
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.dataCols = data.columns.tolist()

    def toStockInfo(self, dateCol: str, symbolCol: str,
                  openCol: str, highCol: str, lowCol: str, closeCol: str,
                  startDateCol: str = None, endDateCol: str = None) -> Dict[str, StockInfo]:
        """
        单个交易日的转换
        stockInfo: InfoDict<String, StockInfo>
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

    def toStockInfos(self, dateCol: str, symbolCol: str,
                  openCol: str, highCol: str, lowCol: str, closeCol: str,
                  startDateCol: str = None, endDateCol: str = None) -> Dict[pd.Timestamp, Dict[str, StockInfo]]:
        """
        多个交易日的转换
        stockInfos: Dict<Date,InfoDict<String,StockInfo>>
        """
        stockInfos = {}
        dateList = sorted(set(self.data[dateCol]))
        nThreads = 8    # 线程数量

        # 定义子任务函数
        def process(date_val):
            # 过滤单个日期
            temp_converter = fromDataFrame(self.data[self.data[dateCol] == date_val])
            # 执行转换
            result = temp_converter.toStockInfo(
                dateCol=dateCol,symbolCol=symbolCol,openCol=openCol,
                highCol=highCol,lowCol=lowCol,closeCol=closeCol,
                startDateCol=startDateCol,endDateCol=endDateCol)
            return date_val, result
            # 将列信息打包

        # 使用线程池执行多线程处理
        with ThreadPoolExecutor(max_workers=nThreads) as executor:
            # 提交所有任务
            futures = {executor.submit(process, date): date for date in dateList}
            # 收集结果
            for future in as_completed(futures):
                date_val, result = future.result()
                stockInfos[date_val] = result
        return stockInfos

    def toFutureInfo(self, dateCol: str, symbolCol: str,
                     openCol: str, highCol: str, lowCol: str, closeCol: str,
                     preSettleCol: str,
                     settleCol: str, startDateCol: str, endDateCol: str) -> Dict[str, FutureInfo]:
        """
        单个交易日的转换
        futureInfo: InfoDict<String, FutureInfo>>
        """
        futureInfo = {}
        for index, row in self.data.iterrows():
            tradeDate = pd.Timestamp(row[dateCol])
            symbol = row[symbolCol]
            open_price = row[openCol]
            high_price = row[highCol]
            low_price = row[lowCol]
            close_price = row[closeCol]
            settle = row[settleCol]
            pre_settle = row[preSettleCol]
            start_date = pd.Timestamp(row[startDateCol])
            end_date = pd.Timestamp(row[endDateCol])
            margin_rate = 0.1   # 由于当前缺少期货合约保证金率 -> 10%代替
            futureInfo[symbol] = FutureInfo(tradeDate, symbol,
                 open_price, high_price, low_price,
                 pre_settle, settle, margin_rate,
                 close_price, start_date, end_date)
        return futureInfo

    def toFutureInfos(self, dateCol: str, symbolCol: str,
                 openCol: str, highCol: str, lowCol: str, closeCol: str,
                 preSettleCol: str, settleCol: str, startDateCol: str, endDateCol: str) -> Dict[pd.Timestamp, Dict[str, FutureInfo]]:
        """
        多个交易日的转换
        futureInfos: Dict<Date,InfoDict<String,FutureInfo>>
        """
        futureInfos = {}
        dateList = sorted(set(self.data[dateCol]))
        nThreads = 8    # 线程数量

        # 定义子任务函数
        def process(date_val):
            # 过滤单个日期
            temp_converter = fromDataFrame(self.data[self.data[dateCol] == date_val])
            # 执行转换
            result = temp_converter.toFutureInfo(
                dateCol=dateCol, symbolCol=symbolCol, openCol=openCol,
                highCol=highCol, lowCol=lowCol, closeCol=closeCol,
                preSettleCol=preSettleCol, settleCol=settleCol,
                startDateCol=startDateCol, endDateCol=endDateCol)
            return date_val, result

        # 使用线程池执行多线程处理
        with ThreadPoolExecutor(max_workers=nThreads) as executor:
            # 提交所有任务
            futures = {executor.submit(process, date): date for date in dateList}
            # 收集结果
            for future in as_completed(futures):
                date_val, result = future.result()
                futureInfos[date_val] = result
        return futureInfos

    def toStockBar(self, isMinBar: bool, dateCol:  str, symbolCol: str,
                  openCol: str, highCol: str, lowCol: str, closeCol: str,
                  volumeCol: str, minuteCol: str = None) -> Dict[pd.Timestamp, Dict[str, dict]]:
        """
        单个交易日的转换
        stockBar: TreeMap<LocalTime, Map<String, Bar>> -> Bar: {"open": "high": "low": "close":}
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

    def toStockBars(self, isMinBar: bool, dateCol:  str, symbolCol: str,
                  openCol: str, highCol: str, lowCol: str, closeCol: str,
                  volumeCol: str, minuteCol: str = None) -> Dict[pd.Timestamp, Dict[pd.Timestamp, Dict[str, dict]]]:
        """
        多个交易日的转换
        stockBar: TreeMap<LocalTime, Map<String, Bar>> -> Bar: {"open": "high": "low": "close":}
        """
        stockBars = {}
        dateList = sorted(set(self.data[dateCol]))
        nThreads = 8  # 线程数量

        # 定义子任务函数
        def process(date_val):
            # 过滤单个日期
            temp_converter = fromDataFrame(self.data[self.data[dateCol] == date_val])
            # 执行转换
            result = temp_converter.toStockBar(
                isMinBar=isMinBar, dateCol=dateCol, symbolCol=symbolCol,
                openCol=openCol, highCol=highCol, lowCol=lowCol,
                closeCol=closeCol, volumeCol=volumeCol, minuteCol=minuteCol)
            return date_val, result

        # 使用线程池执行多线程处理
        with ThreadPoolExecutor(max_workers=nThreads) as executor:
            # 提交所有任务
            futures = {executor.submit(process, date): date for date in dateList}
            # 收集结果
            for future in as_completed(futures):
                date_val, result = future.result()
                stockBars[date_val] = result
        return stockBars


    def toFutureBar(self, isMinBar : bool, dateCol: str, symbolCol: str,
                  openCol: str, highCol: str, lowCol: str, closeCol: str,
                  volumeCol: str, minuteCol: str = None) -> Dict[pd.Timestamp, Dict[str, dict]]:
        """
        单个交易日的转换
        futureBar: TreeMap<LocalTime, Map<String, Bar>> -> Bar: {"open": "high": "low": "close":}
        :param isMinBar: 是否为分钟频Bar
        :param dateCol: 日期列
        :param symbolCol: 标的列
        :param openCol: 开盘价列
        :param highCol: 最高价列
        :param lowCol: 最低价列
        :param closeCol: 收盘价列
        :param volumeCol: 成交量列
        :param minuteCol: 分钟列(可选, isMinBar = true 时必填)
        :return: 
        """
        futureBar = {}
        for index, row in self.data.iterrows():
            tradeDate = pd.Timestamp(row[dateCol])
            if isMinBar:
                tradeTime = pd.Timestamp(row[minuteCol])
            else:
                tradeTime = pd.Timestamp(tradeDate.strftime("%Y%m%d")+ " 15:00:00.000")
            symbol = row[symbolCol]
            open_price = row[openCol]
            high_price = row[highCol]
            low_price = row[lowCol]
            close_price = row[closeCol]
            volume = row[volumeCol]
            if tradeTime not in futureBar:
                futureBar[tradeTime] = {}
            futureBar[tradeTime][symbol] = {"open": open_price, "high": high_price, "low": low_price, "close": close_price, "volume": volume}
        return futureBar

    def toFutureBars(self, isMinBar: bool, dateCol: str, symbolCol: str,
                openCol: str, highCol: str, lowCol: str, closeCol: str,
                volumeCol: str, minuteCol: str = None) -> Dict[pd.Timestamp, Dict[pd.Timestamp, Dict[str, dict]]]:
        """
        多个交易日的转换
        futureBars: Dict<Date, TreeMap<LocalTime, Map<String, Bar>>> -> Bar: {"open": "high": "low": "close":}
        """
        futureBars = {}
        dateList = sorted(set(self.data[dateCol]))
        nThreads = 8  # 线程数量

        # 定义子任务函数
        def process(date_val):
            # 过滤单个日期
            temp_converter = fromDataFrame(self.data[self.data[dateCol] == date_val])
            # 执行转换
            result = temp_converter.toFutureBar(
                isMinBar=isMinBar, dateCol=dateCol, symbolCol=symbolCol,
                openCol=openCol, highCol=highCol, lowCol=lowCol,
                closeCol=closeCol, volumeCol=volumeCol, minuteCol=minuteCol)
            return date_val, result

        # 使用线程池执行多线程处理
        with ThreadPoolExecutor(max_workers=nThreads) as executor:
            # 提交所有任务
            futures = {executor.submit(process, date): date for date in dateList}
            # 收集结果
            for future in as_completed(futures):
                date_val, result = future.result()
                futureBars[date_val] = result
        return futureBars

