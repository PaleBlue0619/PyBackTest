import pandas as pd
from TradeBehavior import TradeBehavior

class CounterBehavior(TradeBehavior):
    def __init__(self):
        super(CounterBehavior, self).__init__()

    def beforeDayFuture(self):
        """更新保证金率至各个仓位->实行资金划拨"""