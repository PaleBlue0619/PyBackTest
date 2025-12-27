import pandas as pd

class Position:
    def __init__(self, symbol: str, price: float, vol: int,
                 min_timestamp: pd.Timestamp, max_timestamp: pd.Timestamp):
        self.symbol = symbol
        self.ori_price = price
        self.vol = vol
        self.min_timestamp = min_timestamp
        self.max_timestamp = max_timestamp

class StockPosition(Position):
    def __init__(self, direction: str, symbol: str, price: float, vol: int,
                 min_timestamp: pd.Timestamp, max_timestamp: pd.Timestamp,
                 static_profit: float, static_loss: float,
                 dynamic_profit: float, dynamic_loss: float):
        super().__init__(symbol, price, vol, min_timestamp, max_timestamp)
        self.direction = direction
        self.sign = 1 if direction == 'long' else -1
        self.ori_price = price
        self.static_profit = static_profit
        self.static_loss = static_loss
        self.dynamic_profit = dynamic_profit
        self.dynamic_loss = dynamic_loss
        self.pre_price = price
        self.profit = 0.0
        self.time_monitor = 0   # 是否需要监控时间, 0: 还没判断过
        self.static_monitor = 0 # 是否需要监控静态止盈止损
        self.static_profit = static_profit
        self.static_loss = static_loss
        if self.sign == 1:
            self.static_high = price * (1 + static_profit) if static_profit else None
            self.static_low = price * (1 - static_loss) if static_loss else None
        else:
            self.static_high = price * (1 + static_loss) if static_loss else None
            self.static_low = price * (1 - static_profit) if static_profit else None
        self.dynamic_monitor = 0 # 是否需要监控动态止盈止损
        self.dynamic_profit = dynamic_profit
        self.dynamic_loss = dynamic_loss
        self.dynamic_high = None
        self.dynamic_low = None
        self.history_max = price
        self.history_min = price

    def onBarUpdate(self, price: float) -> float:
        # 更新历史最高价 & 最低价
        self.history_max = max(self.history_max, price)
        self.history_min = min(self.history_min, price)

        # 更新当前仓位的利润
        realTimeProfit = (price - self.pre_price) * self.vol * self.sign
        self.profit += realTimeProfit
        self.pre_price = price
        return realTimeProfit

    def afterDayUpdate(self):
        # 更新monitor属性
        self.time_monitor = 0
        self.static_monitor = 0
        self.dynamic_monitor = 0
        return realTimeProfit

    def onBarMonitorTime(self, current_date: pd.Timestamp, current_timestamp: pd.Timestamp, end_date: pd.Timestamp):
        """
        :param current_date: 当前日期
        :param current_timestamp: 当前时间戳
        :param end_date: 最后交易日
        :return:
        """
        if self.time_monitor == 0:
            min_date = self.min_timestamp.date()
            max_date = self.max_timestamp.date()
            if min_date < current_date: # T+1
                self.time_monitor = -2
            elif end_date > current_date > min_date and current_date < max_date:
                self.time_monitor = -1  # 在最长持仓时间内 + 期货合约没有结束
            else:
                self.time_monitor = 1   # 正常平仓

        if self.time_monitor == -1: # 今天某个时刻会超过最短持仓时间
            if current_timestamp > self.min_timestamp:
                self.time_monitor = 1

    def onBarMonitorStatic(self, daily_max_price: float, daily_min_price: float):
        """上帝视角加速止盈止损判断"""
        if self.static_monitor == 0:
            if not self.static_high and self.static_low:
                self.static_monitor = -1
            elif not self.static_high and self.static_low > daily_min_price:
                self.static_monitor = -1    # 一定成交不了
            elif not self.static_low and self.static_high < daily_max_price:
                self.static_monitor = -1    # 一定成交不了
            else:
                self.static_monitor = 1

    def onBarMonitorDynamic(self, daily_max_price: float, daily_min_price: float):
        """上帝视角加速止盈止损判断"""
        # 计算当前动态止盈止损价格并进行更新
        if self.sign == 1:  # 多头
            dynamic_high = (1 + self.dynamic_profit) * self.history_min if self.dynamic_profit else None
            dynamic_low = (1 - self.dynamic_loss) * self.history_max if self.dynamic_loss else None
        else:   # 空头
            dynamic_high = (1 + self.dynamic_loss) * self.history_max if self.dynamic_loss else None
            dynamic_low = (1 - self.dynamic_profit) * self.history_min if self.dynamic_profit else None
        self.dynamic_high = dynamic_high
        self.dynamic_low = dynamic_low

        # 第一根K线进行判断
        if self.dynamic_monitor == 0:
            max_price = max(daily_max_price, self.history_max)
            min_price = min(daily_min_price, self.history_min)
            if not self.dynamic_profit and not self.dynamic_loss:
                self.dynamic_monitor = -1   # 不设动态止盈止损
            elif not self.dynamic_profit and (max_price - daily_min_price)/max_price < self.dynamic_loss:
                # 只设动态止损+max(daily_high,history_high)->daily_low的振幅<动态止损比例：今天必然触发不了
                self.dynamic_monitor = -1
            elif not self.dynamic_loss and (daily_max_price - min_price)/min_price < self.dynamic_profit:
                # 只设动态止盈+daily_low->min(daily_low,history_low)->max(daily_high,history_high)的振幅<动态止盈比例：今天必然触发不了
                self.dynamic_monitor = -1
            else:
                self.dynamic_monitor = 1

class FuturePosition(Position):
    def __init__(self, direction: str, symbol: str, price: float, vol: int,
                 pre_settle: float, margin_rate: float,
                 min_timestamp: pd.Timestamp, max_timestamp: pd.Timestamp,
                 static_profit: float, static_loss: float,
                 dynamic_profit: float, dynamic_loss: float):
        super().__init__(symbol, price, vol, min_timestamp, max_timestamp)
        self.direction = direction
        self.sign = 1 if direction == 'long' else -1
        self.ori_price = price
        self.pre_settle = pre_settle
        self.margin_rate = margin_rate
        self.margin = margin_rate * vol * price  # 该仓位的保证金金额
        self.static_profit = static_profit
        self.static_loss = static_loss
        self.dynamic_profit = dynamic_profit
        self.dynamic_loss = dynamic_loss
        self.pre_price = price
        self.profit = 0.0   # 实时盈亏
        self.hold_days = 0
        self.time_monitor = 0   # 是否需要监控时间, 0: 还没判断过
        self.static_monitor = 0 # 是否需要监控静态止盈止损
        self.static_profit = static_profit
        self.static_loss = static_loss
        if self.sign == 1:
            self.static_high = price * (1 + static_profit)
            self.static_low = price * (1 - static_loss)
        else:
            self.static_high = price * (1 + static_loss)
            self.static_low = price * (1 - static_profit)
        self.dynamic_monitor = 0 # 是否需要监控动态止盈止损
        self.dynamic_profit = dynamic_profit
        self.dynamic_loss = dynamic_loss
        self.dynamic_high = None
        self.dynamic_low = None
        self.history_max = price
        self.history_min = price

    def marginRateUpdate(self, margin_rate: float):
        if abs(margin_rate - margin_rate)< 1e-6:
            return 0.0
        margin_diff = (margin_rate - self.margin_rate) * self.vol * self.pre_price
        self.margin -= margin_diff
        self.margin_rate = margin_rate
        return margin_diff

    def onBarUpdate(self, price: float) -> float:
        # 更新历史最高价 & 最低价
        self.history_max = max(self.history_max, price)
        self.history_min = min(self.history_min, price)

        # 更新当前仓位的利润
        realTimeProfit = (price - self.pre_price) * self.vol * self.sign
        self.profit += realTimeProfit
        self.pre_price = price
        return realTimeProfit

    def afterDayUpdate(self, settle: float):
        # 更新monitor属性
        self.time_monitor = 0
        self.static_monitor = 0
        self.dynamic_monitor = 0
        # 更新hold_days
        self.hold_days += 1

        # 更新当前仓位的利润
        realTimeProfit = (self.pre_price - settle) * self.vol * self.sign
        self.profit += realTimeProfit
        self.margin += realTimeProfit
        self.pre_price = settle # 更新当前仓位的pre_price为price
        return realTimeProfit

    def afterDaySettle(self, settle: float):
        """更新结算价"""
        settleProfit = (settle - self.pre_settle) * self.vol * self.sign
        self.pre_settle = settle
        return settleProfit

    def onBarMonitorTime(self, current_date: pd.Timestamp, current_timestamp: pd.Timestamp, end_date: pd.Timestamp):
        """
        :param current_date: 当前日期
        :param current_timestamp: 当前时间戳
        :param end_date: 最后交易日
        :return:
        """
        if self.time_monitor == 0:
            min_date = self.min_timestamp.date()
            max_date = self.max_timestamp.date()
            if min_date < current_date: # T+1
                self.time_monitor = -2
            elif end_date > current_date > min_date and current_date < max_date:
                self.time_monitor = -1  # 在最长持仓时间内 + 期货合约没有结束
            else:
                self.time_monitor = 1   # 正常平仓

        if self.time_monitor == -1: # 今天某个时刻会超过最短持仓时间
            if current_timestamp > self.min_timestamp:
                self.time_monitor = 1

    def onBarMonitorStatic(self, daily_max_price: float, daily_min_price: float):
        """上帝视角加速止盈止损判断"""
        if self.static_monitor == 0:
            if not self.static_high and self.static_low:
                self.static_monitor = -1
            elif not self.static_high and self.static_low > daily_min_price:
                self.static_monitor = -1    # 一定成交不了
            elif not self.static_low and self.static_high < daily_max_price:
                self.static_monitor = -1    # 一定成交不了
            else:
                self.static_monitor = 1

    def onBarMonitorDynamic(self, daily_max_price: float, daily_min_price: float):
        """上帝视角加速止盈止损判断"""
        # 计算当前动态止盈止损价格并进行更新
        if self.sign == 1:  # 多头
            dynamic_high = (1 + self.dynamic_profit) * self.history_min if self.dynamic_profit else None
            dynamic_low = (1 - self.dynamic_loss) * self.history_max if self.dynamic_loss else None
        else:   # 空头
            dynamic_high = (1 + self.dynamic_loss) * self.history_max if self.dynamic_loss else None
            dynamic_low = (1 - self.dynamic_profit) * self.history_min if self.dynamic_profit else None
        self.dynamic_high = dynamic_high
        self.dynamic_low = dynamic_low

        # 第一根K线进行判断
        if self.dynamic_monitor == 0:
            max_price = max(daily_max_price, self.history_max)
            min_price = min(daily_min_price, self.history_min)
            if not self.dynamic_profit and not self.dynamic_loss:
                self.dynamic_monitor = -1   # 不设动态止盈止损
            elif not self.dynamic_profit and (max_price - daily_min_price)/max_price < self.dynamic_loss:
                # 只设动态止损+max(daily_high,history_high)->daily_low的振幅<动态止损比例：今天必然触发不了
                self.dynamic_monitor = -1
            elif not self.dynamic_loss and (daily_max_price - min_price)/min_price < self.dynamic_profit:
                # 只设动态止盈+daily_low->min(daily_low,history_low)->max(daily_high,history_high)的振幅<动态止盈比例：今天必然触发不了
                self.dynamic_monitor = -1
            else:
                self.dynamic_monitor = 1