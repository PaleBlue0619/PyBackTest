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

性能方面，PyBackTest能够实现>10w条K线每秒的回测速度，由于行情与基本信息均在append函数内并行转换为嵌套字典 + 对象管理的订单&仓位Queue + 单例模式管理基本上下文对象+行情数据对象，使得其即使在回测过程中全程单线程处理订单也能发挥较高性能。同时，PyBackTest在分钟频回测中创新性地使用了“上帝视角”，即通过传入日线的信息以加速分钟频订单静态&动态止盈止损方面的判断——提前结束那些当日必定触发不了的无效条件的监视状态。

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
* orderOpenStock: 股票多/空方向开仓指令
* orderOpenFuture: 期货多/空方向开仓指令
* orderCloseStock: 股票多/空方向平仓指令
* orderCloseFuture: 期货多/空方向平仓指令
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
单例模式+面向对象封装，由浅入深可以分为用户层-BackTester-柜台层-核心行为层四个层次
## 2.1 用户层
详见test文件夹下的StockStrategyTest.py与FutureStrategyTest.py文件。以股票日线单因子策略的回测流程为例，PyBackTest典型的回测流程如下:
```python
# 获取配置文件
session = ddb.session()
config = {
    "start_date": "20200101",
    "end_date": "20210101",
    "run_stock": True,
    "run_future": False,
    "freq": 2, # 1(分钟频) # 2(日频)
    "cash": 2000000,
    "stockCash": 1000000,
    "futureCash": 1000000
}
MyFactor = pd.read_feather(r"D:\BackTest\PyBackTest\data\stock_cn\factor\MyFactor.feather")
config["context"] = {
    "MyFactor": MyFactor,
    "dayLongDict": [],  # 每日做多字典{标的:权重}
    "dayShortDict": [] # 每日做空字典{标的:权重}
}
# 构造回调函数字典
eventCallBacksDict = {
    "initialize": initialize,
    "beforeTrading": beforeTrading,
    "afterTrading": afterTrading,
    "onTrade": onTrade,
    "onBar": onBar,
    "finalize": finalize
}
# 创建回测实例
BackTester = BackTester("StockStrategyTest", config, eventCallBacksDict, session=session)
stockBar = pd.read_parquet(r"D:\BackTest\PyBackTest\data\stock_cn\bar")
stockInfo = pd.read_parquet(r"D:\BackTest\PyBackTest\data\stock_cn\info")
# 注入回测实例 -> 自动执行回测
BackTester.append(
    stockBar=stockBar,
    stockInfo=stockInfo,
    futureBar=None,
    futureInfo=None
)
```

## 2.2 BackTester

BackTester层主要是为了将现有的回测逻辑进行用户层-系统层的解耦，即通过BackTester同时交互系统层（柜台层）与用户层（用户级别的回调函数），从而使得用户的回调函数能够快速移植至其他数据源，同时使得用户专注于核心策略逻辑的开发而非回测逻辑的编写。
``` python
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

    def initialize(self):
        """
        用户的初始化函数调用
        """
        # 系统的初始化 -> 构建context上下文
        self.SysContext = Context.get_instance()
        self.SysContext.initialize_from_config(config=self.config)  # 从用户传入的配置中初始化
        self.dataDict = DataDict.get_instance()
        self.UserContext["TradeDate"] = self.start_date
        self.UserContext["TradeTime"] = self.start_date
        self.UserContext["NextDate"] = self.date_list[min(1, len(self.date_list)-1)]

        if "initialize" in self.eventCallbacks:
            initialize_func = self.eventCallbacks["initialize"]
            initialize_func(self, self.UserContext)

    def beforeTrading(self):
        """
        用户级别的beforeTrading调用
        """
        if "beforeTrading" in self.eventCallbacks:
            beforeTrading_func = self.eventCallbacks["beforeTrading"]
            beforeTrading_func(self, self.UserContext)

    def onBar(self, barDict: Dict[str, any]):
        """
        用户级别的onBar调用
        """
        if "onBar" in self.eventCallbacks:
            onBar_func = self.eventCallbacks["onBar"]
            onBar_func(self, self.UserContext, barDict)

    def afterTrading(self):
        """
        用户的afterTrading调用
        """
        if "afterTrading" in self.eventCallbacks:
            afterTrading_func = self.eventCallbacks["afterTrading"]
            afterTrading_func(self, self.UserContext)
    
    def append(self, stockBar: pd.DataFrame = None, stockInfo: pd.DataFrame = None,
               futureBar: pd.DataFrame = None, futureInfo: pd.DataFrame = None):
        """
        由于开发精力有限 -> 这里默认回测到最大时间戳 -> 且以天为单位注入
        :param barData: 区间的Bar数据
        :param infoData: 区间的信息数据
        Step1. 转换为BarDict & InfoDict
        Step2. 提取其中的时间戳+排序 -> for loop进行回测
        """
        ...
```

## 2.3 柜台层
### 1. TradeBehavior行为类
TradeBehavior从交易者角度出发，主要为回测中交易订单->发送到柜台的处理逻辑，Order阶段并未发生任何资金与标的的转移，但需要记录订单的行为(OrderDetails)。
* orderOpenStock(direction, symbol, vol, price, ...)
向柜台发送股票开多/开空订单

* orderCloseStock(direction, symbol, vol, price, ...)
向柜台发送股票平多/平空订单

* orderOpenFuture(direction, symbol, vol, price, ...)
向柜台发送期货开多/开空订单

* orderCloseFuture(direction, symbol, vol, price, ...)
向柜台发送期货平多/平空订单

### 2. CounterBehavior行为类
CounterBehvaior延续了TradeBehavior的视角，包含了所有除撮合订单以外的柜台实时行为。
* beforeDayFuture(): 系统级别的期货盘前回调函数
* afterBarStock(): 系统级别的股票Bar回调函数
* afterBarFuture(): 系统级别的期货Bar回调函数
* afterDayStock(): 系统级别的股票盘后回调函数
* afterDayFuture(): 系统级别的期货盘后回调函数
* afterBarStats(): 系统级别的Bar统计回调函数
* afterDayStats(): 系统级别的每日盘后统计回调函数
* onTrade(): 系统级别的成交回调函数
* openStock(direction, symbol, vol, price, ...): 股票开仓函数
* closeStock(direction, symbol, vol, price, ...): 股票平仓函数
* openFuture(direction, symbol, vol, price, ...): 期货开仓函数
* closeFuture(direction, symbol, vol, price, ...): 期货平仓函数
* monitorStockPosition(direction, symbol, useClose): 系统级别的股票分仓持仓时间+止盈止损监控函数 -> 上帝视角加速判断 + FIFO触发
* monitorFuturePosition(direction, symbol, useClose): 系统级别的期货分仓持仓时间+止盈止损监控函数 -> 上帝视角加速判断 + FIFO触发

### 3. Counter类
Counter类则同时继承了TradeBehavior和CounterBehavior两个类，同时定义了撮合订单的静态方法——这主要是因为撮合订单的算法具有特殊性，后续方便单独定制化改动。


## 2.4 核心层-1: 全局属性
### 1. Context上下文类 <br>

PyBackTest的Context类是单例模式，实际回测中能够避免重复创建不必要的对象实例，减少内存消耗。Context类主要包含了系统级别的相关成员属性以及用户级别的相关成员属性。
```python
class Context:
    _instance = None
    _initialized = False
    _order_num = 0
    _trade_num = 0
    _lock = threading.Lock()

    def __init__(self):
        # 防止重复初始化
        if not Context._initialized:
            ...

    @classmethod
    def get_instance(cls) -> 'Context':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_nextOrderNum(self) -> int:
        """获取全局唯一的自增订单编号"""
        with self._lock:
            self._order_num += 1
            return self._order_num

    def get_nextTradeNum(self) -> int:
        """获取全局唯一的自增成交编号"""
        with self._lock:
            self._trade_num += 1
            return self._trade_num

    def initialize_from_config(self, config: dict):
        """从配置数据初始化"""
        ...
```
### 2. DataDict数据字典类 <br>

DataDict类是单例模式，实际回测中能够避免重复创建DataDict对象实例，减少内存消耗。DataDict类主要包含了系统级别和用户级别数据字典。
```python
class DataDict:
    _instance = None
    _initialized = False
    _order_num = 0
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """防止重复初始化"""
        if not DataDict._initialized:
            DataDict._initialized = True
            # 行情数据
            self.stockKDict = {}  # 股票该日行情字典 TreeMap<LocalTime, Map<String, Bar>>
            self.futureKDict = {} # 期货该日行情字典
            self.optionKDict = {} # 期权该日行情字典

            # 信息数据
            self.stockInfoDict = {}     # 股票该日信息字典
            self.futureInfoDict = {}    # 期货该日信息字典
            self.optionInfoDict = {}    # 期权该日信息字典

    @classmethod
    def get_instance(cls) -> 'DataDict':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    ...(getter & setter method)
```
## 2.5 核心层-2: src.entity.pojo
PyBackTest的pojo主要包括了Order(订单)、OrderDetails(订单记录)、Position(仓位)、Statistics(统计)、Summary(持仓视图)、TradeDetails(成交记录)六个类，具体而言的架构如下:
```
Order
  -StockOrder
    -StockOpenOrder
    -StockCloseOrder
  -FutureOrder
    -FutureOpenOrder
    -FutureCloseOrder
Position:
  -StockPosition
  -FuturePosition
Summary: 持仓视图类-当前该合约/标的的持仓Summary
  -StockSummary
  -FutureSummary
OrderDetails
TradeDetails
Statistics
```
* Order: 订单类 -> 用户向柜台发送的订单信息(包含了最小/最长订单时间 & 最小/最长持仓时间 & 静态与动态止盈止损等信息)
* Position: 仓位类 -> 当前该合约/标的的独立Position,通过getPosition方法可返回某个合约/标的的List[Position] <br>
* Summary: 持仓视图类 -> 当前该合约/标的的Position Summary(方便快速查看该标的/合约的开仓均价&持仓量&现价实时盈亏&持仓情况)
* OrderDetais: 订单记录类 -> 记录用户向柜台发送的订单信息(相对Order仅保留主要信息作为记录)
* TradeDetails: 成交记录类 -> 订单成交信息
* Statistics: 统计类

# 3. 改进方向
按照优先级对改进方向进行排序: <br>
1. 系统级别回调函数 & 操作函数对用户遮掩 <br>
2. 增加onTrade回调函数 <br>
3. 期权分钟频回测相关Context & DataDict成员变量属性 + 下单函数 + 执行函数 + 仓位管理&视图管理函数 <br>