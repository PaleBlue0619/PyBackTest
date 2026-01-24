import json
import threading
from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from src.entity.pojo.Order import StockOrder, FutureOrder
    from src.entity.pojo.Summary import StockSummary, FutureSummary
    from src.entity.pojo.Position import stockPosition, FuturePosition

class Context:
    _instance = None
    _initialized = False
    _order_num = 0
    _trade_num = 0
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 防止重复初始化
        if not Context._initialized:
            Context._initialized = True
            # 用户自定义类
            self.start_date = None
            self.end_date = None
            self.cash = None
            self.stockCash = None
            self.futureCash = None
            self.seed = 42
            self.freq = None
            self.run_stock = False
            self.run_future = False

            # 框架维护的属性
            self.current_date = None
            self.current_minute = None
            self.current_timestamp = None
            self.oriCash = self.cash
            self.oriStockCash = self.stockCash
            self.oriFutureCash = self.futureCash
            self.profit = 0.0   # 平仓盈亏
            self.realTimeProfit = 0.0   # 实时盈亏
            self.stockProfit = 0.0
            self.stockRealTimeProfit = 0.0
            self.futureProfit = 0.0
            self.futureRealTimeProfit = 0.0
            self.futureSettleProfit = 0.0
            self.stockCounter: Dict[int, StockOrder] = {}  # 股票柜台队列
            self.futureCounter: Dict[int, FutureOrder] = {} # 期货柜台队列
            self.stockLongPosition: Dict[str, List[StockPosition]] = {}     # 股票多仓明细
            self.stockShortPosition: Dict[str, List[StockPosition]] = {}    # 股票空仓明细
            self.futureLongPosition: Dict[str, List[FuturePosition]] = {}    # 期货多仓明细
            self.futureShortPosition: Dict[str, List[FuturePosition]] = {}   # 期货空仓明细
            self.stockLongSummary: Dict[str, StockSummary] = {}     # 股票多仓视图
            self.stockShortSummary: Dict[str, StockSummary] = {}    # 股票空仓视图
            self.futureLongSummary: Dict[str, FutureSummary] = {}    # 期货多仓视图
            self.futureShortSummary: Dict[str, FutureSummary] = {}   # 期货空仓视图
            # TODO: 记录类成员变量维护

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
        self.start_date = config["start_date"]
        self.end_date = config["end_date"]
        self.cash = config["cash"]
        self.stockCash = config["stockCash"]
        self.oriStockCash = self.stockCash
        self.futureCash = config["futureCash"]
        self.oriFutureCash = self.futureCash
        self.run_stock = config["run_stock"]
        self.run_future = config["run_future"]