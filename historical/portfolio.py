import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from abc import ABCMeta, abstractmethod
from math import floor

from . event import FillEvent, OrderEvent

from scipy.stats import norm

class Portfolio(object):
    __metaclass__ = ABCMeta

    def __init__(self, bars, initial_capital=10000):
        # create bars and intial capital
        self.bars = bars 
        self.initial_capital = initial_capital

        if self.bars.only_one_ticker == True: # This if handels one ticker or multiple to make portfolio
            self.tickers = list()
            self.tickers.append(self.bars.ticker)
        elif self.bars.only_one_ticker == False: 
            self.tickers = self.bars.tickers
        else: # if only_one_ticker is not defined print error message
            print('____________only_one_ticker varible was not found from datahandler, Please define__________________')
        
        self.port = pd.DataFrame(columns=self.tickers,index=self.bars.df.index)# creates empty PD frame with columns for each ticker and dates from the data
        
        self.all_positions = self.construct_all_positions()
        self.current_positions = dict( (k,v) for k, v in [(s, 0) for s in self.tickers] ) # dict with tickers and units currently owned
        self.all_holdings = self.construct_all_holdings()
        self.current_holdings = self.construct_current_holdings()

    def construct_all_positions(self): # units of product, list of dicts,>> datetime:timestamp, ticker:units
        d = dict( (k,v) for k, v in [(s, 0) for s in self.tickers] )
        d['datetime'] = self.bars.df.index[0]
        return [d]

    def construct_all_holdings(self): # List of dicts, >>> datetime: timestamp, cash:$, commission:$, total:$
        d = dict( (k,v) for k, v in [(s, 0.0) for s in self.tickers] )
        d['datetime'] = self.bars.df.index[0] # takes first index value from first row from bars df 
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return [d]

    def construct_current_holdings(self): # dict >>> tickers:$, cash:$, commission:$, total:$
        d = dict( (k,v) for k, v in [(s, 0.0) for s in self.tickers] )
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return d
    
    def update_portfolio_positions(self):
        """
        Basically the code below is run after the current_positions dict is updated. This makes it easy becuase
        you only need to update the current_positions dictionary throughout using the portfolio class. The only 
        requirement is that update_portfolio_positions neededs to be run after each update of current_positions.
        >> updates all_positions 
        """
        # update current Positions
        position_dict = dict( (k,v) for k, v in [(s, 0) for s in self.tickers])
        position_dict['datetime'] = self.bars.latest_df.index[-1] # takes the latest_df last index location. this values grows when running
        
        for ticker in self.tickers: # transfer values from current_positions dict too temporary positions_dict
            position_dict[ticker] = self.current_positions[ticker] # looping through each item in current positions
        self.all_positions.append(position_dict) #now positions dictionary is updated add it to historical positions

    def update_portfolio_holdings(self):
        if self.bars.only_one_ticker:
            bars = {}   # create bars dict>>> tickers:currentPrice $
            for ticker in self.tickers:
                bars[ticker] = self.bars.get_latest_bars(ticker,N=1)['Open'].values[0]
        elif self.bars.only_one_ticker == False:
            print("__________ add update_portfolio_values for multiple cases inside_upodate_portfolio_holdings_________")
        else: # catch errors in-cases only_one_ticker is not used correctly
            print('_____________update_portfolio_values error probabaly need var only_one_ticker')
        holdings_dict = dict( (k,v) for k, v in [(s, 0) for s in self.tickers] )

        holdings_dict['datetime'] = self.bars.latest_df.index[-1]
        holdings_dict['cash'] = self.current_holdings['cash']
        holdings_dict['commission'] = self.current_holdings['commission']
        
        holdings_value = 0 # used to calcualte total, add each product value ans cash minus commissions
        if self.bars.only_one_ticker:
            # Approximation to the real value
            market_value = float(self.current_positions[ticker]) * float(bars[ticker])  #calculate estimated value in $
            holdings_dict[ticker] = market_value
            holdings_value += market_value
            holdings_dict['total'] = holdings_value + float(self.current_holdings['cash']) - float(self.current_holdings['commission'])
            # Append the current holdings
            self.all_holdings.append(holdings_dict)
        else:
            print("________hadel more than one tikcer case inside update_portfolio_holdings__________")
        
    def update(self): # create update object that balances positions and holdings
        """
        This will be run with each iteration of the generator. This method simplifies updateing the all_positions 
        which are in  units of the product and and all_holdings, with units of  $. Should be run with each market 
        update. 
        """
        self.update_portfolio_positions()
        self.update_portfolio_holdings()


    @abstractmethod
    def update_signal(self, event):
        raise NotImplementedError("Should implement update_signal()")

    @abstractmethod
    def update_fill(self, event):
        raise NotImplementedError("Should implement update_fill()")

    


class BasicPortfolio(Portfolio):
    def __init__(self, bars, events, initial_capital=10000):
        # Holding>$ , Postions>Units of product
        self.bars = bars
        self.events = events

        self.port = Portfolio(bars=bars) # create portfolio objects
        # create (dicts) and (list of dicts) to keep track of portfolio and holdings, 4 total
        self.all_positions = self.port.all_positions # list of dicts >> Units of product >> holds historic postions
        self.current_positions = self.port.current_positions # dict >> units of product >> only holds present positions
        self.all_holdings = self.port.all_holdings # list of dicts >> units of $ >> holds historic holdings
        self.current_holdings = self.port.current_holdings # dict >> units of $ >> only holds present holdings


    def update_signal(self, event):
        """
        Input is a signal to buy an assest. This signal method will determine if anything is owned. If 
        Nothing is currently owned it will evenly distribute the captial between all assests in the bars.
        for example: If one product is fead it will create an order event allocating all the capital to that product.
        If multiple products are fead witht he bars it will ditribute evenly between all of them and create an order
        event for each. 5 products would allocate 20% of captial to each, forming an index benchmark. 
        """
        if event.type == 'SIGNAL': # confirm the event is a signal
            i = 0 # i will be used to add holdings too
            for ticker in self.port.tickers: # add all positions to i
                self.current_positions[ticker] += i
            if i == 0: # if no positions then create a buy hold strategy 
                dollar_amount = self.port.initial_capital/ len(self.port.tickers) # evenly distribute captial to amek index
                for ticker in self.port.tickers:
                    bar = self.bars.get_latest_bars(ticker, N=1) # estimte value, Open is used to avoid look-ahead bias
                    units = dollar_amount / bar['Open'] # calcualte amount of untis for the capital injection
                    order_event = OrderEvent(symbol=ticker, 
                                            order_type='MARKET',
                                            quantity = units,
                                            direction= 'BUY') # order event is created with MARKET order_type
                    self.events.put(order_event) # add each order_event to the Queue

    def fill_update(self, event):
        """
        Handels cases when a purchase or sell is made to portfolio. 
        Starts with updating the current_positions and current_holdings dicts from the fill event. 
        After the current values are updated the commisions and cash values are adjusted. 
        Finally port.update is applied to add these values to the all_positions and all_holdings
        """
        # Update current_positions dict >> units of the product
        if event.direction == 'BUY': # if buying add units to current_positions
            self.current_positions[event.symbol] = event.quantity # units updated
        elif event.direction == 'SELL':# is selling minus the units from current_positions
            self.current_positions[event.symbol] = - event.quantity # units updated
        else:
            print('_____fill_update    not buy or sell?')
        
        # Update current_holidngs dict >> commisions, cash ,total, and values-$
        if event.direction == 'BUY': # buy and sell are trated seperatly 
            if self.bars.only_one_ticker == True: # only one ticker to avoide error because no col labeled Open with multiple currencies df
                transaction_dollar_amount = self.bars.get_latest_bars(event.symbol,N=1)['Open'] * event.quantity
                self.current_holdings[event.symbol] += transaction_dollar_amount
            else: 
                print('add case for multiple fill_update__________________')

            self.current_holdings['cash'] -= float(transaction_dollar_amount) # when its a buy always subtract buys from avilble capital
            self.current_holdings['commission'] = float(event.fill_cost)
            # add>> cash, holdings, and subtract commisions to calcualte total>>$
            self.current_holdings['total'] = self.current_holdings[event.symbol] + self.current_holdings['cash'] - self.current_holdings['commission']

        elif event.direction == 'SELL':
            pass 
        else:
            print('_________fill_update seems to not have buy or sell  var posss')
   

    def update_fill(self, event):
        if event.type == 'MARKET': # if market just update values
            self.port.update()
        if event.type == 'FILL': # if fill must balance portfolio also
            #fill update to current holdings
            self.fill_update(event=event) # only updates current_positions and current_holdings
            self.port.update() # once current dicts updated update historic postfolio values. 

        
    


     
        
       





class BenchMarkPortfolio(Portfolio):
    def __init__(self, bars, events, start_date, initial_capital=100000.0):
        self.bars = bars
        self.events = events
        self.symbol_list = self.bars.symbol_list
        self.start_date = start_date
        self.initial_capital = initial_capital
        
        self.all_positions = self.construct_all_positions()
        self.current_positions = dict( (k,v) for k, v in [(s, 0) for s in self.symbol_list] )

        self.all_holdings = self.construct_all_holdings()
        self.current_holdings = self.construct_current_holdings()

    def construct_all_positions(self):#working
        d = dict( (k,v) for k, v in [(s, 0) for s in self.symbol_list] )
        d['datetime'] = self.start_date
        return [d]

    def construct_all_holdings(self): #working
        d = dict( (k,v) for k, v in [(s, 0.0) for s in self.symbol_list] )
        d['datetime'] = self.start_date
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return [d]

    def construct_current_holdings(self): #working
        d = dict( (k,v) for k, v in [(s, 0.0) for s in self.symbol_list] )
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return d

    def update_portfolio_values(self, event):
        bars = {}
        for sym in self.symbol_list:
            bars[sym] = self.bars.get_latest_bars(sym, N=1).values[0]
        # Update positions
        dp = dict( (k,v) for k, v in [(s, 0) for s in self.symbol_list] )
        dp['datetime'] = self.bars.get_latest_time()
        for s in self.symbol_list:
            dp[s] = self.current_positions[s]
        # Append the current positions
        self.all_positions.append(dp) # add to historic positions
        # Update holdings
        dh = dict( (k,v) for k, v in [(s, 0) for s in self.symbol_list] )
        dh['datetime'] = self.bars.get_latest_time()
        dh['cash'] = self.current_holdings['cash']
        dh['commission'] = self.current_holdings['commission']
        dh['total'] = self.current_holdings['cash']
        
        for s in self.symbol_list:
            # Approximation to the real value
            market_value = self.current_positions[s] * bars[s]  #calculate estimated value in $
            dh[s] = market_value
            dh['total'] += market_value
        # Append the current holdings
        self.all_holdings.append(dh)

    def update_positions_from_fill(self, fill):
        # Check whether the fill is a buy or sell
        fill_dir = 0
        if fill.direction == 'BUY':
            fill_dir = 1
        if fill.direction == 'SELL':
            fill_dir = -1

        # Update positions list with new quantities
        self.current_positions[fill.symbol] += fill_dir * fill.quantity

    def update_holdings_from_fill(self, fill):
        # Check whether the fill is a buy or sell
        fill_dir = 0
        if fill.direction == 'BUY':
            fill_dir = 1
        if fill.direction == 'SELL':
            fill_dir = -1
        # Update holdings list with new quantities
        fill_cost = self.bars.get_latest_bars(fill.symbol).values[0]  # Close price
        cost = fill_dir * fill_cost * fill.quantity
        self.current_holdings[fill.symbol] += cost
        self.current_holdings['commission'] += fill.commission
        self.current_holdings['cash'] -= (cost + fill.commission)
        self.current_holdings['total'] -= (cost + fill.commission)

    def update_fill(self, event):
        if event.type == 'FILL':
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)

    def generate_naive_order(self, signal):

        order = None
        if signal.symbol == None:
            pass
        else:
            symbol = signal.symbol
            direction = signal.signal_type
            amount_allocated =  self.initial_capital / len(self.symbol_list)
            mkt_quantity = amount_allocated / self.bars.get_latest_bars(symbol, N=1).values[0]

            cur_quantity = self.current_positions[symbol]
            order_type = 'MARKET'
            if direction == 'LONG' and cur_quantity == 0:
                order = OrderEvent(symbol, order_type, mkt_quantity, 'BUY')
            if direction == 'SHORT' and cur_quantity == 0:
                order = OrderEvent(symbol, order_type, mkt_quantity, 'SELL')   
        
            if direction == 'EXIT' and cur_quantity > 0:
                order = OrderEvent(symbol, order_type, abs(cur_quantity), 'SELL')
            if direction == 'EXIT' and cur_quantity < 0:
                order = OrderEvent(symbol, order_type, abs(cur_quantity), 'BUY')
            
            print('Buy ', symbol,' quantity = ', mkt_quantity)
            return order

    def update_signal(self, event):
        if event.type == 'SIGNAL':
            order_event = self.generate_naive_order(event)
            self.events.put(order_event)
            
    def create_equity_curve_dataframe(self):
        curve = pd.DataFrame(self.all_holdings)
        curve.set_index('datetime', inplace=True)
        curve['returns'] = curve['total'].pct_change()
        curve['equity_curve'] = (1.0+curve['returns']).cumprod()
        return curve
    
    def _create_df(self):
        df = pd.DataFrame(self.all_holdings)
        df = df.set_index('datetime')
        return df 

    def _sharpe_ratio(self,df, N=90):
        return np.sqrt(N) * df.mean() / df.std()

    def _rolling_sharpe_ratio(self):
        df  = self._create_df()
        df['returns'] = df['total'].pct_change(1)
        df['bench_rs']  = df['returns'].rolling(window =90).apply(self._sharpe_ratio,raw=True)
        return df['bench_rs']

    def _cumulative_return(self):
        df  = self._create_df()
        cumulative_return = 100 * (df['total'][-1:][0] / df['total'][:1][0])
        print('cumulative return = ',cumulative_return,'%')
        return cumulative_return
    
    def _var_cov_var(self,P, c, mu, sigma):
        alpha = norm.ppf(1-c, mu, sigma)
        return P - P*(alpha + 1)

    def var_99(self):
        df = self._create_df()
        port_change = df['total'].pct_change()
        P = df['total'][-1:][0]
        c= 0.99
        mu = np.mean(port_change)
        sigma = np.std(port_change)
        var = self._var_cov_var(P, c, mu, sigma)
        return var

    def max_draw_down(self):
        df = self._create_df()
        drawdown_df = pd.DataFrame()
        window = 252
        roll_max = df['total'].rolling(window).max()
        daily_drawdown = df['total']/ roll_max - 1.0
        drawdown_df['Bench Daily Draw Down %']  = daily_drawdown
        return drawdown_df
      
class TrainClassificationModelPortfolio(Portfolio):
    def __init__(self,bars, events, start_date, initial_capital=100000.0):
        self.bars = bars
        self.events = events
        self.start_date = start_date
        self.initial_capital = initial_capital

        self.ticker_list = self.bars.symbol_list
        self.current_units = self._create_current_units()
        self.current_value = self._create_current_value()
        self.all_units = self._create_all_units()
        self.all_values = self._create_all_values()

        self.ticker_owned = ''
    
    def update_portfolio_values(self):
        #create bars to calculate value
        bars = {}
        for sym in self.ticker_list:
            bars[sym] = self.bars.get_latest_bars(sym, N=1)
            bars['datetime'] = bars[self.ticker_list[0]].index[0]
        # Update units
        dp = dict( (k,v) for k, v in [(s, 0) for s in self.ticker_list] )
        dp['datetime'] = bars[self.ticker_list[0]].index[0]
        for s in self.ticker_list:
            dp[s] = self.current_units[s]
        self.all_units.append(dp)
        ###############################################################################
        # Update VALUE
        dh = dict( (k,v) for k, v in [(s, 0) for s in self.ticker_list] )
        dh['datetime'] = bars[self.ticker_list[0]].index[0]
        dh['cash'] = self.current_value['cash']
        dh['commission'] = self.current_value['commission']
        dh['total'] = self.current_value['cash']

        for s in self.ticker_list:
            # Approximation to the real value
            market_value = self.current_units[s] * bars[s][0]
            dh[s] = market_value
            dh['total'] += market_value
        self.all_values.append(dh)
 
    def _create_current_units(self):
        d = dict( (k,v) for k, v in [(s, 0) for s in self.ticker_list] )
        d['datetime'] = self.start_date
        return d
    
    def _create_all_units(self):
        d = dict( (k,v) for k, v in [(s, 0) for s in self.ticker_list] )
        d['datetime'] = self.start_date
        return [d]
    
    def _create_current_value(self):
        d = dict( (k,v) for k, v in [(s, 0.0) for s in self.ticker_list] )
        d['datetime'] = self.start_date
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return d
    
    def _create_all_values(self):
        d = dict( (k,v) for k, v in [(s, 0.0) for s in self.ticker_list] )
        d['datetime'] = self.start_date
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return [d]
    
    def _update_units_from_fill(self, event):
        # Check whether the fill is a buy or sell
        fill_dir = 0
        if event.direction == 'BUY':
            fill_dir = 1
        if event.direction == 'SELL':
            fill_dir = -1
        # Update positions list with new quantities
        self.current_units[event.symbol] += fill_dir * event.quantity
    
    def _update_values_from_fill(self,event):
        total = 0.0
        fill_dir = 0
        if event.direction == 'BUY':
            fill_dir = 1
        if event.direction == 'SELL':
            fill_dir = -1
        # Update holdings list with new quantities
        fill_cost = self.bars.get_latest_bars(event.symbol)[0] # Close price
        cost = fill_dir * fill_cost * event.quantity
        self.current_value[event.symbol] += cost
        self.current_value['commission'] += event.commission
        self.current_value['cash'] -= (cost + event.commission)
        for ticker in self.ticker_list:
            total += self.current_value[ticker]
        total += self.current_value['cash']
        total -= self.current_value['commission']
        self.current_value['total'] = total

    def create_equity_curve_dataframe(self):
        curve = pd.DataFrame(self.all_values)
        curve.set_index('datetime', inplace=True)
        curve['returns'] = curve['total'].pct_change()
        curve['equity_curve'] = (1.0+curve['returns']).cumprod()
        return curve
      
    def update_fill(self,event):
        if event.type =='FILL':
            self._update_units_from_fill(event)
            self._update_values_from_fill(event)

    def update_signal(self,event):
        if event.symbol==None:
            pass
        else:
            #first case, own nothing all in cash 
            if self.ticker_owned =='':
                order_type = 'MKT'
                mkt_quantity = self.current_value['cash']/self.bars.get_latest_bars(event.symbol)[0]
                order = OrderEvent(event.symbol, order_type, mkt_quantity, 'BUY')
                self.events.put(order)
                print('Buy ', event.symbol,' quantity = ', mkt_quantity)
                self.ticker_owned = event.symbol

            if self.current_units[event.symbol]==0 and self.current_value['cash']==0:
                if self.ticker_owned == event.symbol:
                    pass
                else:
                    order_type = 'MKT'
                    mkt_quantity = self.current_units[self.ticker_owned]
                    order = OrderEvent(self.ticker_owned, order_type, mkt_quantity, 'SELL')
                    self.events.put(order)
                    print('SELL ', self.ticker_owned,' quantity = ', mkt_quantity)

                    mkt_quantity = self.all_values[-1]['total']/ self.bars.get_latest_bars(event.symbol)[0]
                    order = OrderEvent(event.symbol, order_type, mkt_quantity, 'BUY')
                    self.events.put(order)
                    self.ticker_owned = event.symbol
                    print('Buy ', event.symbol,' quantity = ', mkt_quantity)
    
    def _create_df(self):
        df = pd.DataFrame(self.all_values)
        df = df.set_index('datetime')
        return df 

    def _sharpe_ratio(self,df, N=90):
        return np.sqrt(N) * df.mean() / df.std()

    def _rolling_sharpe_ratio(self):
        df  = self._create_df()
        df['returns'] = df['total'].pct_change(1)
        df['rs']  = df['returns'].rolling(window =90).apply(self._sharpe_ratio,raw=True)
        return df['rs']

    def _cumulative_return(self):
        df  = self._create_df()
        cumulative_return = 100 * (df['total'][-1:][0] / df['total'][:1][0])
        print('cumulative return = ',cumulative_return,'%')
        return cumulative_return
    
    def _var_cov_var(self,P, c, mu, sigma):
        alpha = norm.ppf(1-c, mu, sigma)
        return P - P*(alpha + 1)

    def var_99(self):
        df = self._create_df()
        port_change = df['total'].pct_change()
        P = df['total'][-1:][0]
        c= 0.99
        mu = np.mean(port_change)
        sigma = np.std(port_change)
        var = self._var_cov_var(P, c, mu, sigma)
        return var

    def max_draw_down(self):
        df = self._create_df()
        drawdown_df = pd.DataFrame()
        window = 252
        roll_max = df['total'].rolling(window).max()
        daily_drawdown = df['total']/ roll_max - 1.0
        drawdown_df['Algo Daily Draw Down %']  = daily_drawdown
        return drawdown_df