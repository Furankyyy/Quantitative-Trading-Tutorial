from zipline import run_algorithm
from zipline.api import order_target_percent, symbol
from datetime import datetime
import pytz
from talib import MACD, ADX, PLUS_DI, MINUS_DI
import pyfolio as pf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


def initialize(context):

    stock_list = ['AAPL','FB','AMZN','NFLX','GOOGL']
    context.universe = [symbol(x) for x in stock_list]

    # Moving average window
    context.index_average_window = 100

def handle_data(context, data):
    context.hold = {stock:False for stock in context.universe}

    # Request history for the stock
    history = data.history(context.universe, ["high","low","close"], context.index_average_window, "1d")
    for i in range(5):

        high = np.array(history['high'].iloc[:,i])
        low = np.array(history['low'].iloc[:,i])
        close = np.array(history['close'].iloc[:,i])

        plus = PLUS_DI(high, low, close, timeperiod=14)
        minus = MINUS_DI(high, low, close, timeperiod=14)
        adx = ADX(high, low, close, timeperiod=14)

        if plus[-1] > minus[-1]:
            if adx[-1] >= 25:
                order_target_percent(history['close'].columns[i], 0.2)
                context.hold[history['close'].columns[i]] = True
            if adx[-1] <= 20:
                order_target_percent(history['close'].columns[i], 0.0)
        if plus[-1] <= minus[-1]:
            order_target_percent(history['close'].columns[i], 0.0)   


def analyze(context, perf):
    returns, positions, transactions = pf.utils.extract_rets_pos_txn_from_zipline(perf)
    pf.create_returns_tear_sheet(returns,benchmark_rets=None,return_fig=True)
    plt.savefig('backtest_adx.png')


if __name__=='__main__':
    start_date = pd.Timestamp(datetime(2014, 1, 1, tzinfo=pytz.UTC))
    end_date = pd.Timestamp(datetime(2017, 12, 31, tzinfo=pytz.UTC))

    run_algorithm(start=start_date,
                  end=end_date,
                  initialize=initialize,
                  analyze=analyze,
                  handle_data=handle_data,
                  capital_base=10000,
                )