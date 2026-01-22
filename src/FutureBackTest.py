"""
完整的PyBackTest实现期货回测实例
"""
import os, json, json5
import time
import pandas as pd
from src.entity.Counter import *
from src.service.getdata.fromDataFrame import fromDataFrame
pd.set_option('display.max_columns', None)

if __name__ == "__main__":
    startDate = "2020.01.01"
    endDate = "2021.01.01"
    barPath = r"D:\\BackTest\\PyBackTest\\data\\future_cn\\bar"
    infoPath = r"D:\\BackTest\\PyBackTest\\data\\future_cn\\info"
    configPath = r"D:\BackTest\PyBackTest\src\backtest_config.json"

    with open(configPath, "r") as f:
        config = json5.load(f)
    context = Context.get_instance()
    context.initialize_from_config(config)
    dataDict = DataDict.get_instance()
    t0 = time.time()
    for tradeDate in [pd.Timestamp("20200102"),
                      pd.Timestamp("20200103"),
                      pd.Timestamp("20200106")]:
        # 获取数据
        barDF = pd.read_parquet(os.path.join(barPath, tradeDate.strftime("%Y%m%d")+".pqt"))
        infoDF = pd.read_parquet(os.path.join(infoPath, tradeDate.strftime("%Y%m%d")+".pqt"))
        futureBarDict = fromDataFrame(barDF).toFutureBar(False, "TradeDate", "symbol", "open", "high", "low", "close", "volume", None)
        futureInfoDict = fromDataFrame(infoDF).toFutureInfo("tradeDate", "symbol", "open_price", "high_price", "low_price", "close_price",
                                                            "pre_settle", "settle", "start_date", "end_date")
        print(barDF[barDF["symbol"]=="A2001.DCE"])
        # 基本属性赋值
        context.current_date = tradeDate
        context.current_minute = pd.Timestamp(tradeDate.strftime("%Y%m%d")+" 15:00:00.000")
        context.current_timestamp = pd.Timestamp(tradeDate.strftime("%Y%m%d")+" 15:00:00.000")
        dataDict.set_futureKDict(futureBarDict)
        dataDict.set_futureInfoDict(futureInfoDict)
        # 柜台下单及处理
        Counter.beforeDayFuture()   # 期货保证金变动处理
        Counter.orderOpenFuture(direction="long", symbol="A2001.DCE", vol=1000, price=3375, static_profit=None, static_loss=None,
                                dynamic_profit=None, dynamic_loss=None, min_order_timestamp=context.current_timestamp, max_order_timestamp=pd.Timestamp("20200105"),
                                min_timestamp=context.current_timestamp, max_timestamp=pd.Timestamp("20250101"), commission=0.0005, partial_order=False, reason="testOpen")
        Counter.orderCloseFuture(direction="long", symbol="A2001.DCE", vol=1000, price=3380, min_order_timestamp=context.current_timestamp,
                                 max_order_timestamp=pd.Timestamp("20200105"), partial_order=False, reason="testClose")
        Counter.processFutureOrder(1.0,1.0)
        Counter.afterBarFuture()
        Counter.monitorFuturePosition("long",True)
        Counter.monitorFuturePosition("short",True)
        Counter.afterDayFuture()
        print(context.cash)
    t1 = time.time()
    print(f"{t1-t0}s")
    print(context.futureRealTimeProfit, context.futureProfit, context.profit)
    print(context.futureLongSummary)