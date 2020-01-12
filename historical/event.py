

class Event(object):
    pass

class MarketEvent(Event):
    def __init__(self):
        self.type = 'MARKET'

class SignalEvent(Event):
    def __init__(self, symbol, datetime, signal_type):
        self.type = 'SIGNAL'
        self.symbol = symbol
        self.datetime = datetime
        self.signal_type = signal_type

class OrderEvent(Event):
    def __init__(self, symbol, order_type, quantity, direction):
        self.type='ORDER'
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.direction = direction

    def print_order(self):
        print("Order: Symbol=%s, Type=%s, Quantity=%s, Direction=%s" % \
            (self.symbol, self.order_type, self.quantity, self.direction))

class FillEvent(Event):
    def __init__(self, timeindex, symbol, exchange, quantity, 
                 direction, fill_cost, commission=None):
        self.type = 'FILL'
        self.timeindex = timeindex
        self.symbol = symbol
        self.exchange = exchange
        self.quantity = quantity
        self.direction = direction
        self.fill_cost = fill_cost

        # Calculate commission
        if commission is None:
            self.commission = 0.0 # calculate_ib_commission
        else:
            self.commission = commission

    def calculate_ib_commission(self):
        def __init__(self, timeindex, symbol, exchange, quantity, direction, fill_cost, commission=None):
        
            full_cost = 1.3
            if self.quantity <= 500:
                full_cost = max(1.3, 0.013 * self.quantity)
            else: # Greater than 500
                full_cost = max(1.3, 0.008 * self.quantity)
            full_cost = min(full_cost, 0.5 / 100.0 * self.quantity * self.fill_cost)
            return full_cost
