import pandas as pd
import numpy as np
from abc import ABCMeta, abstractmethod
from . models import Strategy, BackTestRun, Equity
from django.core.exceptions import ObjectDoesNotExist




class Stats(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def create_stats(self, portfolio):
        raise NotImplementedError("Should implement create_stats()")

    @abstractmethod
    def load_db(self):
        raise NotImplementedError("Should implement load_db()")


            

class PortfolioStatisticsLoader(Stats):
    def __init__(self,save=True, rolling_minutes=1440):
        self.save = save
        self.rolling_minutes = rolling_minutes # 24 hours * 60 min  = 1440 min per day default

    def create_portfolio_dataframe(self):
        # creates pd DF columns = ['tickers', 'cash', 'commission', 'total']
        self.portfolio_df = pd.DataFrame(self.portfolio.all_holdings) # create dataframe with holdings
        self.portfolio_df.set_index('datetime',inplace=True)
        return self.portfolio_df
    
    def rolling_sharpe_function(self, returns):
        return np.sqrt(self.rolling_minutes) * (returns.mean() / returns.std()) # 24 hours * 60 min  = 1440 min per day 

    def rolling_sharpe(self):
        self.portfolio_df['rs'] = self.portfolio_df['total'].pct_change().rolling(self.rolling_minutes).apply(self.rolling_sharpe_function)
        return self.portfolio_df

    def max_dd(self, returns):
        returns = pd.Series(returns)
        max2here = returns.cummax()
        dd2here = returns - max2here
        return dd2here.min() * 100

    def rolling_max_drawdown(self):
        self.portfolio_df['rolling_DD'] = self.portfolio_df['total'].pct_change().rolling(self.rolling_minutes).apply(self.max_dd, raw=True)
       

    def create_stats(self, portfolio):
        self.portfolio = portfolio
        self.create_portfolio_dataframe()
        self.rolling_sharpe()
        self.rolling_max_drawdown()
        print(self.portfolio_df.min(axis=0))
        print(self.portfolio_df.max(axis=0))
    

    def load_db(self,name,description,products):
        # strategy, BackTestRun, Equity
        try:
            s = Strategy.objects.get(name=name,# check if the backtest is already loaded
                                    description=description,
                                    products_traded=products) 
            s.delete() # if loaded delete the startegy. This will cascade and delete all the benchmarkruns
        except ObjectDoesNotExist:
            Strategy.objects.create(name=name,
                                description=description,
                                products_traded=products)
        else:
            # no error, it was sucessfully deleted, Now create it 
            Strategy.objects.create(name=name,
                                description=description,
                                products_traded=products)

        s = Strategy.objects.get(name=name,# check if the backtest is already loaded
                                description=description,
                                products_traded=products) 
        equities = list(self.portfolio_df.columns)
        for item in ['total','commission','rs','rolling_DD']:
            equities.remove(item)
        for index, row in self.portfolio_df.iterrows(): 
            print('saving ', index)
            try: # when dulpliate is attempted causes error. Try will catch these attemps and keep moving foward. 
                run = BackTestRun(strategy=s,
                                    date=index,
                                    total=row['total'],
                                    commission=row['commission'],
                                    rolling_sharpe=row['rs'],
                                    draw_down=row['rolling_DD'])
                run.save()
                for equity in equities:
                    e = Equity(strategy=s,
                        name=str(equity),
                        value=row[equity],
                        date=index)
                    e.save()
        
            except:
                pass
     
