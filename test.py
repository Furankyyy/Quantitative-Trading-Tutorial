from zipline.api import order_target, record, symbol, set_commission, order_percent, set_benchmark, order_target_percent, set_slippage
from zipline.finance import commission
from zipline import run_algorithm
import talib as ta


def initialize(context):

  # Stocks to trade
  stock_list = ['FB', 'AMZN', 'AAPL', 'NFLX', 'GOOGL']
  context.stocks = [symbol(stock) for stock in stock_list]

  # How much of the portfolio is invested in each stock (20% each)
  context.target_pct_per_stock = 1 / len(context.stocks)

  # Transaction costs
  #context.set_commission(commission.PerShare(cost=0.0, min_trade_cost=0))
  #context.set_commission(commission.PerDollar(cost=0.0015)) # default is 0.0015
  #context.set_commission(commission.PerTrade(cost=0.0))

  # Slippage
  #context.set_slippage(slippage.VolumeShareSlippage())

  # Upper and Lower bound for RSI trading signals
  context.low_rsi = 30
  context.high_rsi = 70

  # Moving average window
  #context.index_average_window = 100

  set_benchmark(False)

def handle_data(context, data):

  # Historical data
  prices = data.history(context.stocks, 'price', bar_count=20, frequency='1d')
  
  rsis = {}

  # Loop thru the stocks and determine when to buy and sell them
  for stock in context.stocks:
    rsi = ta.RSI(prices[stock], timeperiod=14)[-1]
    rsis[stock] = rsi
  
    current_position = context.portfolio.positions[stock].amount

    if rsi > context.high_rsi and current_position > 0 and data.can_trade(stock):
      order_target(stock, 0)
    elif rsi < context.low_rsi and current_position == 0 and data.can_trade(stock):
      order_target_percent(stock, context.target_pct_per_stock)

  
  record(fb_rsi=rsis[symbol('FB')],
         amzn_rsi=rsis[symbol('AMZN')],
         aapl_rsi=rsis[symbol('AAPL')],
         nflx_rsi=rsis[symbol('NFLX')],
         googl_rsi=rsis[symbol('GOOGL')])


if __name__=='__main__':
    start_date = pd.Timestamp(datetime(2015, 1, 1, tzinfo=pytz.UTC))
    end_date = pd.Timestamp(datetime(2018, 1, 1, tzinfo=pytz.UTC))

    run_algorithm(start=start_date,
                  end=end_date,
                  initialize=initialize,
                  handle_data=handle_data,
                  capital_base=10000,
                )
