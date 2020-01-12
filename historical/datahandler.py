import datetime
import os, os.path
import pandas as pd
from django_pandas.io import read_frame
from abc import ABCMeta, abstractmethod
from historical.event import MarketEvent
from API.models import Product, HistoricRate
from historical.event import MarketEvent


class DataHandler(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_latest_bars(self, symbol, N=1):
        raise NotImplementedError("Should implement get_latest_bars()")

    @abstractmethod
    def update_bars(self):
        raise NotImplementedError("Should implement update_bars()")
    

class DataHandlerOneProductPostgres(DataHandler):
    def __init__(self,ticker):
        product = Product.objects.get(base_currency=ticker)
        data = HistoricRate.objects.filter(product=product).only('date')
        self.continue_backtest= True
        # data
        pass
    def get_latest_bars(self):
        pass
    def update_bars(self):
        pass


class MasterDataHandlerOneProduct(DataHandler):
    """
    1. The update_bars() will feed the latest_df adding a row with each iteration
    2. The get_latest_bars() can be used to make calcualtions within the strategy class and pulls from the latest_df
        -Note! this DataHandler can only feed price data for one ticker that must be provided. 
    """
    def __init__(self,events=None, ticker=None, minutes=1000):
        self.only_one_ticker = True
        self.ticker = ticker
        self.minutes = minutes
        if self.ticker != None:
            self.df = self._one_ticker_df()
        else:
            print('___________Need to supply ticker___________________')
        if events ==None:
            print('___________Need to supply events queue_____________')
        self.events = events
   
        self.latest_df = pd.DataFrame(columns=self.df.columns)
        self.continue_backtest = True
        self.iterator =self._get_new_bar()

    def _one_ticker_df(self):
        #creates pandas DF with for one product
        product = Product.objects.get(base_currency = self.ticker)
        data = HistoricRate.objects.filter(product=product)[:self.minutes] 
        self.df = read_frame(data)
        self.df.set_index('date',inplace=True)
        return self.df

    def get_latest_bars(self, ticker, N=1):
        if self.only_one_ticker == True:
            return self.latest_df[-N:]
        elif self.only_one_ticker == False:
            return self.latest_df[ticker][-N:]
        else:
            print('error in get_latest_bars >> try to define only_one_ticker var posibly.')

    def _get_new_bar(self):
        for index, row in self.df.iterrows():
            yield  index, row
    

    def update_bars(self):
        # index, row = self.iterator.__next__()
        # print(row)
        try:
            index, row = self.iterator.__next__()
        except StopIteration:
            self.continue_backtest = False
        except Exception:
            print('something went wrong')
        else:
            self.latest_df.loc[index] = row
            self.events.put(MarketEvent())
            

