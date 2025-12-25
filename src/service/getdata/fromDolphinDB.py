import os
import dolphindb as ddb
import pandas as pd
from typing import Dict
from joblib import Parallel, delayed # 多进程
from concurrent.futures import ThreadPoolExecutor # 多线程

class fromDolphinDB:
    def __init__(self, session: ddb.session,
                 dataDB: str, dataTB: str, transDict: Dict[str, any]):
        self.session = session
        self.dataDB = dataDB
        self.dataTB = dataTB
        self.transDict = transDict  # 数据表字段名 -> 映射至内存中的名称

class toParquet(fromDolphinDB):
    def __init__(self, dateCol:str, savePath: str, startDate: pd.Timestamp = None, endDate: pd.Timestamp = None,
                 **kwargs):
        super().__init__(
            kwargs.get("session"),
            kwargs.get('dataDB'),
            kwargs.get('dataTB'),
            kwargs.get('transDict', {})
        )
        self.dateCol = dateCol
        self.dateList = []
        startDotDate = startDate.strftime("%Y.%m.%d")
        endDotDate = endDate.strftime("%Y.%m.%d")
        if startDate is not None and endDate is not None:
            self.dateList = self.session.run(f"""
                select count(*) from loadTable("{self.dataDB}","{self.dataTB}") 
                where {dateCol} between {startDotDate} and {endDotDate}
                group by {dateCol} as TradeDate
            """)["TradeDate"].tolist()
            self.dateList = sorted([pd.Timestamp(date) for date in self.dateList
                             if pd.Timestamp(date) >= startDate and date <= endDate])
        self.savePath = savePath
        if not os.path.exists(self.savePath):
            os.makedirs(self.savePath)

    def process(self, date: pd.Timestamp):
        """
        DolphinDB Table -> Parquet<Date>(same filePath)
        """
        # 每个线程内部的处理函数
        print(f"processing date {date}")
        s = ddb.session()
        s.connect(self.session.host, self.session.port, self.session.userid, self.session.password)
        dateStr = date.strftime("%Y%m%d")
        dateDotStr = date.strftime("%Y.%m.%d")
        colNames = list(self.transDict.keys())
        transNames = list(self.transDict.values())
        script = f"""
            colNames = {colNames};
            transNames = {transNames};
            <select _$$colNames as _$$transNames from loadTable("{self.dataDB}","{self.dataTB}") where {self.dateCol} = {dateDotStr}>.eval()
        """
        df = s.run(script,disableDecimal=True)
        df.to_parquet(os.path.join(self.savePath, dateStr+".pqt"))

    def processTotal(self, fileName: str) -> int:
        """
        DolphinDB Table -> Parquet
        """
        fileName = fileName.replace(".pqt","").replace(".parquet","")
        s = ddb.session()
        s.connect(self.session.host, self.session.port, self.session.userid, self.session.password)
        colNames = list(self.transDict.keys())
        transNames = list(self.transDict.values())
        script = f"""
            colNames = {colNames};
            transNames = {transNames};
            <select _$$colNames as _$$transNames from loadTable("{self.dataDB}","{self.dataTB}")>.eval()
        """
        df = s.run(script,disableDecimal=True)
        df.to_parquet(os.path.join(self.savePath, fileName+".pqt"))
        return 0

    def run(self, n_jobs: int = 10):
        """
        多线程处理
        """
        if not self.dateList:
            self.processTotal(fileName="total")
            return

        with ThreadPoolExecutor(max_workers=n_jobs) as executor:
            state = executor.map(self.process, self.dateList)

if __name__ == "__main__":
    session = ddb.Session()
    session.connect("172.16.0.184",8001,"maxim","dyJmoc-tiznem-1figgu")
    trans_dict = {
        "code": "symbol",
        "tradeDate": "TradeDate",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume"
    }
    source = toParquet(
        dateCol="tradeDate",
        savePath="D:/BackTest/PyBackTest/data/stock_cn/bar",
        startDate=pd.Timestamp("2020-01-01"),
        endDate=pd.Timestamp("2021-01-01"),
        dataDB="dfs://MinKDB",
        dataTB="TuStockDayK",
        transDict=trans_dict,
        session=session
    )
    source.run(n_jobs=10)
