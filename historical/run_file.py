
from queue import Queue


class RunClass():
    """
    The run file puts each of the classes together 
    :DataHandler,Predictor, Strategy, Portfolio, Broker
    1: DataHandler will feed data checking for event objects with each iteration
    2: The Prdictor will use a trained model to predict future prices
    3: These predictions take place in the strategy class inherted from predictor
    4: The strategy will  buy and sell signals to the portfolio class
    5: Portfolio class takes care of portfolio allocation portion
    6: After Portfolio approves a buy or sell the signal is set to the broker
    7: Broker will return a order once the order is placed or cancel after certain amount of time
    8: One recipe is returned the portfolio holding are updated within the database. 
    """
    def __init__(self, datahandler, strategy, portfolio, broker, stats, name, description, products):
       # , Portfolio, Strategy, Predictor, Broker
        self.bars = datahandler
        self.strategy = strategy
        self.portfolio = portfolio
        self.broker = broker
        self.stats = stats
        # Information for saving strategy's
        self.name = name # name of strategy
        self.description = description # description of strategy
        self.products = [products] # list of str tickers
    
        # self.broker = Broker
        self._back_test()
        self._run_stats()
    
    def _back_test(self):
        while True:
            print('not breaking')
            if self.bars.continue_backtest == True:
                self.bars.update_bars()
                while True:
                  
                    try:
                        event = self.bars.events.get(False)
                    except Exception:
                        break 
                    else:
                        if event is not None:
                            if event.type == "MARKET":
                                self.strategy.calculate_signal(event=event)
                                self.portfolio.update_fill(event)
                            elif event.type == 'SIGNAL':
                                self.portfolio.update_signal(event)
                            elif event.type == 'ORDER':
                                print('order_event____________-')
                                self.broker.execute_order(event)
                            elif event.type == 'FILL':
                                self.portfolio.update_fill(event)
            else:
                break
        # self.stats.create_stats(self.portfolio)
        # self.stats.load_db()

    def _run_stats(self):
        self.stats.create_stats(self.portfolio)
        print('loading dddddBBBBBBBBB')
        self.stats.load_db(name=self.name,
                         description= self.description,
                         products=self.products)
        
    
    