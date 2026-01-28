# 1. 项目介绍
目前JavaBackTest暂停维护(数据反序列化不友好)，PyBackTest(后续视情况开发CppBackTest)为主要回测工具。

功能方面，PyBackTest目前支持股票/期货的分钟级别及以上的回测需求，未来将加入对于分钟级别及以上买卖期权回测的支持(但不打算支持行权)。在回测特性上，PyBackTest采用了较为主流的context上下文字典+回调函数的形式，在快速实现策略开发的基础上保留了不同数据源下的策略移植性。PyBackTest当前的功能特性汇总如下：<br>
```
1. 股票/期货/股票&期货 + 分钟频/日频的回测
2. context上下文 + 多种回调函数 + 多种操作函数
3. 分段回测 -> 单个回测引擎允许多次按照时间顺序append数据
4. 最短/最长持仓时间+静态/动态止盈止损 (均为分仓设置 + FIFO触发)
5. 支持时变保证金率, 并在保证金率变化当日盘前自动实现资金划拨
```

性能方面，PyBackTest能够实现>10w条K线每秒的回测速度，由于行情与基本信息均在append函数内并行转换为嵌套字典 + 对象管理的订单&仓位Queue，使得其即使在回测过程中全程单线程处理订单也能发挥较高性能。同时，PyBackTest在分钟频回测中创新性地使用了“上帝视角”，即通过传入日线的信息以加速分钟频订单静态&动态止盈止损方面的判断——提前结束那些当日必定触发不了的无效条件的监视状态。

准确性方面, 股票&期货的日频回测demo正确性已通过检验，感兴趣的读者可自行运行test目录下的示例并进行比对。<br>

最后，特别感谢DolphinDB Backtest回测插件在接口设计上给予本项目的规范化参考: <br> https://docs.dolphindb.cn/zh/plugins/backtest/interface_description.html

## 1.1 回测引擎类
BackTester 为本回测引擎创建类 <br>
```python
from src.entity.Context import Context
from src.entity.DataDict import DataDict
from src.entity.Counter import Counter
from src.entity.CounterBehavior import CounterBehavior
from typing import Callable, List, Dict
import dolphindb as ddb # 使用其交易日历功能

class BackTester(Counter, CounterBehavior):
    def __init__(self, name:str, config:Dict[str, any], eventCallbacks:Dict[str, Callable], session:ddb.session):
        self.name = name
        self.config = config
        self.UserContext = config["context"] # 用户级别上下文字典
        self.eventCallbacks = eventCallbacks
        self.SysContext:Context = None   # 系统级别上下文字典
        self.dataDict:DataDict = None  # 行情字典
        self.start_date = config["start_date"]
        self.end_date = config["end_date"]
        self.date_list = session.run(f"""
        startDate = {pd.Timestamp(self.start_date).strftime("%Y.%m.%d")}
        endDate = {pd.Timestamp(self.end_date).strftime("%Y.%m.%d")}
        table(getMarketCalendar("CFFEX",startDate,endDate) as `tradeDay)
        """)["tradeDay"].tolist()
        self.initialize()   # 创建回测引擎的时候进行初始化
```

## 1.2 支持的用户级别回调函数:<br>
* initialize: 策略开始回调函数 <br>
* beforeTrading: 盘前回调函数 <br>
* onBar: Bar 回调函数 <br>
* afterTrading: 盘后回调函数 <br>
* finalize: 策略结束回调函数 <br>
* onTrade: 成交回调函数 <br>

## 1.3 支持的用户级别操作函数:<br>
* getStockSummary: 获取对应方向的股票持仓视图 <br>
* getFutureSummary: 获取对应方向的期货持仓视图(会比getFuturePosition更快, 若只需要确认是否持仓可以调用) <br>
* getStockPosition: 获取对应方向的股票持仓队列(适用于网格类对价格Queue敏感的策略) <br>
* getFuturePosition: 获取对应方向的期货持仓队列(适用于网格类对价格Queue敏感的策略) <br>
* getOrderDetails: 获取至今的订单记录 <br>
* getTradeDetails: 获取至今的交易记录 <br>
* getTradeStatistics: 获取至今的交易pnl统计 <br>
* getAvailableCash: 获取当前分账户资金 <br>
* append: 注入数据(开始自动回测) <br>
* cancelOrder: 撤单函数【后续支持】<br>

## 1.4 PyBackTest需要的数据结构:<br>
PyBackTest参照DolphinDB回测插件appendQuotationMsg的设计思路，设计了append函数，即单个回测引擎能够允许多次数据按照时间顺序注入回测引擎，注入回测引擎后自动开始回测。<br>(https://docs.dolphindb.cn/zh/plugins/backtest/interface_description.html#ariaid-title3)
```python
def append(self, stockBar: pd.DataFrame = None, stockInfo: pd.DataFrame = None, futureBar: pd.DataFrame = None, futureInfo: pd.DataFrame = None):
    """
    由于开发精力有限 -> 这里默认回测到最大时间戳 -> 且以天为单位注入
    :param barData: 区间的Bar数据
    :param infoData: 区间的信息数据
    Step1. 转换为BarDict & InfoDict
    Step2. 提取其中的时间戳+排序 -> for loop进行回测
    """
    ...
```
股票stockBar <br>
* 日K Bar: <br>

|TradeDate|symbol|open|high|low|close|volume|
|----|----|----|----|----|----|----|
|pd.Timestamp|str|float|float|float|float|int|

* 分钟 K Bar: <br>

|TradeDate|TradeTime|symbol|open|high|low|close|volume|
|----|----|----|----|----|----|----|----|
|pd.Timestamp|pd.Timestamp|str|float|float|float|float|int|
<br>

股票stockInfo <br>
|TradeDate|symbol|open_price|high_price|low_price|close_price|pre_settle|settle|start_date|end_date|
|----|----|----|----|----|----|----|----|----|----|
|pd.Timestamp|str|float|float|float|float|float|float|pd.Timestamp|pd.Timestamp|
<br>

期货futureBar <br>
* 日K Bar: <br>

|TradeDate|symbol|open|high|low|close|volume|
|----|----|----|----|----|----|----|
|pd.Timestamp|str|float|float|float|float|int|

* 分钟 K Bar: <br>

|TradeDate|TradeTime|symbol|open|high|low|close|volume|
|----|----|----|----|----|----|----|----|
|pd.Timestamp|pd.Timestamp|str|float|float|float|float|int|
<br>

期货futureInfo <br>
|TradeDate|symbol|open_price|high_price|low_price|close_price|pre_settle|settle|start_date|end_date|multi|
|----|----|----|----|----|----|----|----|----|----|----|
|pd.Timestamp|str|float|float|float|float|float|float|pd.Timestamp|pd.Timestamp|int|
<br>

# 2. 代码结构
面向对象封装，由浅入深可以分为用户层-BackTester-柜台层-核心行为层四个层次
## 2.1 用户层

## 2.2 BackTester

## 2.3 柜台层

## 2.4 核心层次层


# 3. 改进方向
按照优先级对改进方向进行排序: <br>
1. 系统级别回调函数 & 操作函数对用户遮掩 <br>
2. 增加onTrade回调函数 <br>
3. 期权分钟频回测相关Context & DataDict成员变量属性 + 下单函数 + 执行函数 + 仓位管理&视图管理函数 <br>