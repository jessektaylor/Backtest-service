from django.db import models

# Create your models here.
from django.db import models
from django.db.models import Transform
from model_utils import FieldTracker
from asgiref.sync import async_to_sync





class Strategy(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField()
    products_traded = models.CharField(max_length=500)

    def __str__(self):
        return self.name

class BackTestRun(models.Model):
    """
    Stores the portfolio values over time and stores some statistics
    """
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    date = models.DateTimeField()
    total = models.FloatField(default=0)
    commission = models.FloatField(default=0)
    rolling_sharpe = models.FloatField(default=0)
    draw_down = models.FloatField(default=0)
    
    class Meta:
        unique_together = ['strategy', 'date', 'total','commission', 'rolling_sharpe', 'draw_down']

    def __str__(self):
        return self.strategy.name

class Equity(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    name = models.CharField(max_length=25)
    value = models.FloatField(default=0)
    date = models.DateTimeField()

    def __str__(self):
        return self.name




class MySQLDatetimeDate(Transform):
    """
    This implements a custom SQL lookup when using `__date` with datetimes.
    To enable filtering on datetimes that fall on a given date, import
    this transform and register it with the DateTimeField.
    """
    lookup_name = 'datetime'

    def as_sql(self, compiler, connection):
        lhs, params = compiler.compile(self.lhs)
        return 'DATE({})'.format(lhs), params

    @property
    def output_field(self):
        return models.DateField()
        

######################################################
#add acess to Database-service

class Product(models.Model):
    tracker = FieldTracker(fields=('currency_pair',))
    currency_pair = models.CharField(max_length=10)
    base_currency = models.CharField(max_length=10)
    quote_currency = models.CharField(max_length=10)
    base_min_size = models.FloatField(default=0)
    base_max_size = models.FloatField(default=0)
    quote_increment = models.FloatField(default=0)

    def product_list(self):
        product_list = []
        products = Product.objects.all()
        for product in products:
            product_list.append(product.base_currency)
        return product_list

    def currency_pair_list(self):
        currency_pair_list = []
        products= Product.objects.all()
        for product in products:
            currency_pair_list.append(product.currency_pair)
        return currency_pair_list 

    def __str__(self):
        return self.currency_pair

    

    class Meta:
        ordering = ('base_currency',)

class ProductInfo(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    date_created = models.DateTimeField()
    consecutive_missing_avg = models.FloatField(default=0)
    consecutive_missing_max = models.FloatField(default=0)
    percent_missing = models.FloatField(default=0)
    total_days = models.IntegerField(default=0)
    total_minutes = models.BigIntegerField(default=0)
    

    def __str__(self):
        return self.product.base_currency

    class Meta:
        ordering = ('product',)

class HistoricRate( models.Model):
    tracker = FieldTracker(fields=('date',)) # used to overide save method below. Only used to track when changes are made to the date field
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    date = models.DateTimeField()
    time = models.BigIntegerField(default=0)
    low = models.FloatField(default=0)
    high = models.FloatField(default=0)
    Open = models.FloatField(default=0)
    close = models.FloatField(default=0)
    volume = models.FloatField(default=0)

    class Meta:
        unique_together = ['product','date','time','low','high','Open','close','volume']

    def save(self, *args, **kwargs): #Override save method so it sends a message to the channel layer when a update happens
        ret = super().save(*args, **kwargs)
        has_changed = self.tracker.has_changed('date') # tracker import is used to see when the data has changed. 
        """
        BELOW is imported inside the method to prevent circle import error. 
        Serializers imported in notifications depend on models. and models.py uses  notifications.py
        which depend on import from models. 
        """
        from API.notifications import recive_historic_rate_update
        if has_changed:
            async_to_sync(recive_historic_rate_update)(self) # send the instance that we saved to the coresponding function inside notifications.py
        return ret

    def __str__(self):
        return self.product.currency_pair

class DayHistoric(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    date = models.DateTimeField()
    time = models.BigIntegerField(default=0)
    low = models.FloatField(default=0)
    high = models.FloatField(default=0)
    Open = models.FloatField(default=0)
    close = models.FloatField(default=0)
    volume = models.FloatField(default=0)

    class Meta:
        unique_together = ['product','date','time','low','high','Open','close','volume']

    def __str__(self):
        return self.product.currency_pair

class HourHistoric(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    date = models.DateTimeField()
    low = models.FloatField(default=0)
    high = models.FloatField(default=0)
    Open = models.FloatField(default=0)
    close = models.FloatField(default=0)
    volume = models.FloatField(default=0)

    class Meta:
        unique_together = ['product','date']

    def __str__(self):
        return self.product.currency_pair