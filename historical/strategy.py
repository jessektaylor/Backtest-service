from . event import SignalEvent
from abc import ABCMeta, abstractmethod

class Strategy():
    __metaclass__ = ABCMeta

    @abstractmethod
    def calculate_signals(self):
        raise NotImplementedError("Should implement calculate_signals()")

class BuyAndHoldStrategy(Strategy):
    def __init__(self, bars=None, events=None, name=None, description=None):
        if bars ==None:
            print('________________ Strategy class needs bars as input ______________')
        if events ==None:
            print('__________________need to supply event to strategy__________')
        self.bars = bars
        self.events = events
        self.tickers_owned_dict = self.owned_dict() # Dict, Boolean value with ticker as key 
    
    def owned_dict(self):
        """
        created dict with false initaly set for all tickers in the bar object.
        This can accept sigal or multiple tickers. 
        """
        if self.bars.only_one_ticker == True:
            self.tickers= self.bars.ticker
        if self.bars.only_one_ticker == False:
            self.tickers = self.bars.tickers
        self.tickers_owned_dict = {}

        if type(self.tickers)==list:
            for ticker in self.tickers:
                self.tickers_owned_dict[ticker] = False
        elif type(self.tickers) == str:
                self.tickers_owned_dict[self.tickers] = False
        else:
            print('owned_dict attribute must be be supplied ticker in str or list format')
        return self.tickers_owned_dict
            
    def calculate_signal(self, event):
        if event.type == 'MARKET':
            for ticker in list(self.tickers_owned_dict):
                if  self.tickers_owned_dict[ticker] == False:
                    signal = SignalEvent(symbol=ticker,
                                        datetime=self.bars.latest_df.index[0],
                                        signal_type='LONG')
                    self.events.put(signal)
                    self.tickers_owned_dict[ticker] = True

         