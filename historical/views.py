from django.shortcuts import render
from django_pandas.io import read_frame
import pandas as pd
from queue import *
from . models import Strategy, BackTestRun, Equity
from django.http import HttpResponse

from historical.datahandler import MasterDataHandlerOneProduct
from historical.broker import SimulatedExecutionHandler
from historical.statistics import PortfolioStatisticsLoader
from historical.strategy import BuyAndHoldStrategy
from historical.portfolio import BasicPortfolio
from historical.run_file import RunClass



# Create your views here.
def test(request):
    events_q =  Queue()

    bars = MasterDataHandlerOneProduct(ticker='ALGO',
                            events=events_q,
                            minutes=1000)
    strat = BuyAndHoldStrategy(bars=bars,
                            events=events_q)
    portfolio = BasicPortfolio(bars=bars, events=events_q)
    broker = SimulatedExecutionHandler(bars=bars,events=events_q)
    stats = PortfolioStatisticsLoader(save=False)

    RunClass(datahandler=bars,
            strategy=strat,
            portfolio=portfolio,
            broker=broker,
            stats=stats,
            # information for saving
            name = 'Buy and Hold Method',
            description = 'buys equal amount of each equity',
            products = str(bars.ticker))
    return HttpResponse('Load Database task was created')
