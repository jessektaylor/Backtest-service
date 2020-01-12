import datetime

from abc import ABCMeta, abstractmethod
from . event import FillEvent, OrderEvent



class ExecutionHandler(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def execute_order(self, event):
        raise NotImplementedError("Should implement execute_order()")

class SimulatedExecutionHandler(ExecutionHandler):
    def __init__(self, bars, events):
        self.events = events
        self.bars  =  bars 

    def execute_order(self, event):
        if event.type == 'ORDER': 
            # below gets current price multiplies by units multipled by half %, brokrage fee for takers on coinbase pro
            fill_cost = self.bars.get_latest_bars(event.symbol, N=1)['Open'] * event.quantity * .005
            # fill event is filled no matter what in simulation. In reality not everthing is filled . 
            fill_event = FillEvent(timeindex=datetime.datetime.utcnow(),
                                    symbol= event.symbol,
                                    exchange='Coinbase' ,
                                    quantity= event.quantity,
                                    direction= event.direction,
                                    fill_cost=fill_cost)
            self.events.put(fill_event) # add fill event to 