import pandas as pd
import numpy as np
import dolphindb as ddb
pd.set_option("display.max_columns",None)

if __name__ == "__main__":
    session = ddb.session("172.16.0.184", 8001, "maxim", "dyJmoc-tiznem-1figgu")
    df = pd.read_parquet(r"D:\BackTest\PyBackTest\data\future_cn\bar")
    # 只看黄金 & 原油 + 排除TAS指令&期权
    slice_df = df[df["symbol"].apply(
        lambda x:(str(x).startswith("SC") or str(x).startswith("AU")) and (len(str(x).split(".")[0])<=6))
    ].reset_index(drop=True)
    # 每日主力合约数据表
    mainContractDF = session.run("""
    select ts_code_body as product, trade_date as TradeDate, mapping_ts_code as symbol from loadTable("dfs://DayKDB", "o_tushare_futures_mian_and_contract")
    """)
    mainContractDF.to_feather(r"D:\BackTest\PyBackTest\data\future_cn\main\mainContract.feather")
    print(mainContractDF)
    print(slice_df)
