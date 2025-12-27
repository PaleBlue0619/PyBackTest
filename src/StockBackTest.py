"""
完整的PyBackTest实现股票回测实例
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
    barPath = r"D:\\BackTest\\PyBackTest\\data\\stock_cn\\bar"
    infoPath = r"D:\\BackTest\\PyBackTest\\data\\stock_cn\\info"
    configPath = r"D:\\BackTest\\JavaBackTest\\src\\main\\java\\com\\maxim\\backtest_config.json"

    with open(configPath, "r") as f:
        config = json5.load(f)
    context = Context.get_instance()
    context.initialize_from_config(config)
    dataDict = DataDict.get_instance()
    t0 = time.time()
    for tradeDate in [pd.Timestamp("20200102"),
                      pd.Timestamp("20200103"),
                      pd.Timestamp("20200106")]:
        # 准备数据
        barDF = pd.read_parquet(os.path.join(barPath, tradeDate.strftime("%Y%m%d")+".pqt"))
        infoDF = pd.read_parquet(os.path.join(infoPath, tradeDate.strftime("%Y%m%d")+".pqt"))
        stockBarDict = fromDataFrame(barDF).toStockBar(False, "TradeDate", "symbol", "open", "high", "low", "close", "volume", None)
        stockInfoDict = fromDataFrame(infoDF).toStockInfo("TradeDate", "symbol", "open_price", "high_price", "low_price", "close_price", "start_date", "end_date")
        print(barDF[barDF["symbol"]=="000001.SZ"])
        print(infoDF[infoDF["symbol"]=="000001.SZ"])
        # 基本属性赋值
        context.current_date = tradeDate
        context.current_minute = pd.Timestamp(tradeDate.strftime("%Y%m%d")+" 15:00:00.000")
        context.current_timestamp = pd.Timestamp(tradeDate.strftime("%Y%m%d")+" 15:00:00.000")
        dataDict.set_stockKDict(stockBarDict)
        dataDict.set_stockInfoDict(stockInfoDict)
        Counter.orderOpenStock(direction="long", symbol="000001.SZ", vol=100, price=17.00, static_profit=None, static_loss=None,
                          dynamic_profit=None, dynamic_loss=None,
                          min_order_timestamp=context.current_timestamp, max_order_timestamp=pd.Timestamp("20250101"),
                          min_timestamp=context.current_timestamp, max_timestamp=pd.Timestamp("20250101"),
                          commission=0.0005, partial_order=False, reason="testOpen")
        Counter.processStockOrder(1.0,1.0)
        Counter.afterBarStock()
        Counter.monitorStockPosition("long",True)
        Counter.monitorStockPosition("short",True)
        Counter.afterDayStock()
    # print(context.cash, context.stockCash)
    # print(context.stockLongPosition)
    print(context.stockLongSummary["000001.SZ"].__dict__)
    # for pos in context.stockLongPosition["000001.SZ"]:
    #     print(pos.__dict__)
    # t1 = time.time()
    # print(f"{t1-t0}s")
    #



