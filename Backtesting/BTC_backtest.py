import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


### BTC Long-Short
'''
#step1
def load_data(csv_name):
    df = pd.read_csv(csv_name, parse_dates=['timestamp'])
    return df

#step 2
def create_features(df):
    df['day'] = df.timestamp.dt.weekday
    return df

#step 3
def to_position(day_int):
    if day_int >= 4:
        return 1
    else:
        return -1


def generate_signals(df):
    df['entry'] = df.day.apply(to_position)
    return df



#step4
def calculate_returns(df):
    #step4.1
    df['returns'] = np.log(df.close/df.close.shift(1))
    #step 4.2
    df['strategy_returns'] = df.entry * df.returns

    #step4.3
    df['strat_total'] = df.strategy_returns.cumsum()

    df['bench_total'] = df.returns.cumsum()

    return df




def run_backtest(csv_name, init_invest):
    df = load_data(csv_name)

    df = create_features(df)

    df = generate_signals(df)

    df= calculate_returns(df)
    #plot strategy vs bench
    df.set_index('timestamp')
    df[['strat_total','bench_total']].plot()
    plt.show()

    strat_prof = np.exp(df.strat_total.values[-1])
    bench_prof = np.exp(df.bench_total.values[-1])

    print(f"Strategy initial invest: ${init_invest} ending: ${init_invest*strat_prof}")
    print(f"Bench initial invest: ${init_invest} ending: ${init_invest *bench_prof}")

    return df


if __name__ == '__main__':
    csv_name = 'data/cleaned_btc.csv'
    init_invest = 100

    df = run_backtest(csv_name, init_invest)
'''


### Backtest class (general)

class BackTestSA:
    '''
    backtesting class for all single asset strategies, 
    columns must include the following :
    close: float
    timestamp: date
    '''

    def __init__(self, dataframe, max_holding):
        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError('Dataframe must be pandas df')

        #vertical barrier variable
        self.max_holding = max_holding
        self.max_holding_limit = max_holding

        self.df = dataframe

        #trade variables
        self.open_pos = False
        self.entry_price = None
        self.direction = None
        self.target_price = None
        self.stop_price = None

        #barrier multipliers
        self.ub_mult = 1.005
        self.lb_mult = 0.995
        
        #special case of vertical barrier
        self.end_date = self.df.timestamp.values[-1]

        self.returns_series = []


    def open_long(self, price):
        '''
        :param price: price we open long at
        :return: populates trade variables from constructor with relevant variables
        '''
        self.open_pos = True
        self.direction = 1
        self.entry_price = price
        self.target_price = price * self.ub_mult
        self.stop_price = price * self.lb_mult
        self.returns_series.append(0)

    def open_short(self, price):
        '''
        
        :param price: price we open short at
        :return: populates trade variables from constructor with relevant variables
        '''
        self.open_pos = True
        self.direction = -1
        self.entry_price = price
        self.target_price = price * self.lb_mult
        self.stop_price = price * self.ub_mult
        self.returns_series.append(0)

    def reset_variables(self):
        '''
        resets the variables after we close a trade
        '''
        self.open_pos = False
        self.entry_price = None
        self.direction = None
        self.target_price = None
        self.stop_price = None
        self.max_holding = self.max_holding_limit

    def close_position(self, price):
        '''
        :param price: price we are exiting trade at 
        :return: appends the trade pnl to the returns series 
        and resets variables 
        '''
        pnl = (price/self.entry_price-1)*self.direction
        self.returns_series.append(pnl)
        self.reset_variables()


    def generate_signals(self):
        '''
        use this function to make sure generate signals has been included in the child class 
        '''
        if 'entry' not in self.df.columns:
            raise Exception('You have not created signals yet')


    def monitor_open_positions(self, price, timestamp):
        #check upper horizontal barrier for long positions
        if price >= self.target_price and self.direction == 1:
            self.close_position(price)
        #check lower horizontal barrier for long positions
        elif price <= self.stop_price and self.direction == 1:
            self.close_position(price)
        # check lower horizontal barrier for short positions
        elif price <= self.target_price and self.direction == -1:
            self.close_position(price)
        # check upper horizontal barrier for short positions
        elif price >= self.stop_price and self.direction == -1:
            self.close_position(price)
        # cehck special case of vertical barrier
        elif timestamp == self.end_date:
            self.close_position(price)
        # check vertical barrier
        elif self.max_holding <= 0:
            self.close_position(price)
        # if all above conditions not true, decrement max holding by 1 and append a zero to returns column
        else:
            self.max_holding = self.max_holding - 1
            self.returns_series.append(0)


    def run_backtest(self):
        #signals generated from child class
        self.generate_signals()
        
        #loop over dataframe 
        for row in self.df.itertuples():
            #if we get a long signal and do not have open position open a long
            if row.entry == 1 and self.open_pos is False:
                self.open_long(row.close)
            #if we get a short position and do not have open position open a sort
            elif row.entry == -1 and self.open_pos is False:
                self.open_short(row.close)
            #monitor open positions to see if any of the barriers have been touched, see function above
            elif self.open_pos:
                self.monitor_open_positions(row.close, row.timestamp)
            else:
                self.returns_series.append(0)



### BTC Moving average crossover

class MovingAverageStrategy(BackTestSA):

    def __init__(self, dataframe, max_holding):
        super().__init__(dataframe, max_holding)



    def generate_signals(self):

        df = self.df

        df['ma_20'] = df.close.rolling(20).mean()
        df['ma_50'] = df.close.rolling(50).mean()

        df['ma_diff'] = df.ma_20 - df.ma_50

        df['longs'] = ((df.ma_diff > 0) & (df.ma_diff.shift(1) < 0))*1
        df['shorts'] = ((df.ma_diff < 0) & (df.ma_diff.shift(1) > 0)) * -1

        df['entry'] = df.longs + df.shorts

        self.df = df


    def show_performace(self):
        rets = np.array(self.returns_series)

        cum_rets = rets.cumsum()

        plt.plot(cum_rets)
        plt.show()

'''
if __name__ == '__main__':
    dataframe = pd.read_csv('data/cleaned_btc.csv')

    max_holding = 180

    m = MovingAverageStrategy(dataframe, max_holding)

    m.run_backtest()
    m.show_performace()
    print('Total strategy return:',np.cumsum(m.returns_series)[-1]*100,'%')
'''

if __name__ == '__main__':
    dataframe = pd.read_csv('data/SPY.csv')

    max_holding = 10

    m = MovingAverageStrategy(dataframe, max_holding)

    m.run_backtest()
    m.show_performace()
    print('Total strategy return:',np.cumsum(m.returns_series)[-1]*100,'%')