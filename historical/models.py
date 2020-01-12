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
        

