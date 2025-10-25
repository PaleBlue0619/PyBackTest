import pandas as pd

class Summary:
    def __init__(self, ori_price: float, total_vol: int,
                 static_profit: float, static_loss: float,
                 dynamic_profit: float, dynamic_loss: float):
        self.ori_price = ori_price
        self.total_vol = total_vol
        self.static_profit = static_profit
        self.static_loss = static_loss
        self.dynamic_profit = dynamic_profit
        self.dynamic_loss = dynamic_loss

class StockSummary(Summary):
    def __init__(self, direction: str, ori_price: float, total_vol: int,
                static_profit: float, static_loss: float,
                dynamic_profit: float, dynamic_loss: float):
        super().__init__(ori_price, total_vol, static_profit, static_loss, dynamic_profit, dynamic_loss)
        self.direction = direction
        self.sign = 1 if direction == 'long' else -1
        self.dynamic_monitor = 0
        self.static_monitor = 0
        self.profit = 0.0
        self.realTimeProfit = 0.0
        self.realTimePrice = ori_price

    # 开仓回调函数
    def openUpdate(self, price: float, vol: int, static_profit: float, static_loss: float, dynamic_profit: float, dynamic_loss: float):
        self.static_profit = static_profit
        self.static_loss = static_loss
        self.dynamic_profit = dynamic_profit
        self.dynamic_loss = dynamic_loss

        # 更新vol
        ori_price = self.ori_price
        vol0 = self.total_vol
        amount0 = vol0 * ori_price
        vol1 = vol0 + vol
        amount1 = amount0 + price * vol

        # 赋值回summary
        self.total_vol = vol
        self.ori_price = amount1 / vol1

    # 平仓回调函数
    def closeUpdate(self, price: float, vol: int):
        """
        以price 卖出 vol后
        """
        self.total_vol -= vol
        self.profit += (price - self.ori_price) * vol * 1 # 累计盈亏
        self.realTimeProfit = (price - self.ori_price) * self.total_vol * self.sign # 更新最新利润

    # K线回调函数
    def onBarUpdate(self, price: float):
        self.realTimePrice = price
        self.realTimeProfit = (price - self.ori_price) * self.total_vol * self.sign

    # 盘后结算回调函数
    def afterDayUpdate(self, settle: float):
        self.realTimePrice = settle
        self.realTimeProfit = (settle - self.ori_price) * self. total_vol * self.sign


class FutureSummary(Summary):
    def __init__(self, direction: str, ori_price: float, total_vol: int,
                static_profit: float, static_loss: float,
                dynamic_profit: float, dynamic_loss: float):
        super().__init__(ori_price, total_vol, static_profit, static_loss, dynamic_profit, dynamic_loss)
        self.direction = direction
        self.sign = 1 if direction == 'long' else -1
        self.dynamic_monitor = 0
        self.static_monitor = 0
        self.profit = 0.0
        self.realTimeProfit = 0.0
        self.realTimePrice = ori_price

    # 开仓回调函数
    def openUpdate(self, price: float, vol: int, static_profit: float, static_loss: float, dynamic_profit: float, dynamic_loss: float):
        self.static_profit = static_profit
        self.static_loss = static_loss
        self.dynamic_profit = dynamic_profit
        self.dynamic_loss = dynamic_loss

        # 更新vol
        ori_price = self.ori_price
        vol0 = self.total_vol
        amount0 = vol0 * ori_price
        vol1 = vol0 + vol
        amount1 = amount0 + price * vol

        # 赋值回summary
        self.total_vol = vol
        self.ori_price = amount1 / vol1

    # 平仓回调函数
    def closeUpdate(self, price: float, vol: int):
        """
        以price 卖出 vol后
        """
        self.total_vol -= vol
        self.profit += (price - self.ori_price) * vol * 1 # 累计盈亏
        self.realTimeProfit = (price - self.ori_price) * self.total_vol * self.sign # 更新最新利润

    # K线回调函数
    def onBarUpdate(self, price: float):
        self.realTimePrice = price
        self.realTimeProfit = (price - self.ori_price) * self.total_vol * self.sign

    # 盘后结算回调函数
    def afterDayUpdate(self, settle: float):
        self.realTimePrice = settle
        self.realTimeProfit = (settle - self.ori_price) * self. total_vol * self.sign
