from django.contrib import admin

# Register your models here.
from django.contrib import admin
from . models import Strategy, BackTestRun, Equity



class StrategyAdmin(admin.ModelAdmin):
    list_display = ('name','description','products_traded')
    list_filter = ('name',)
admin.site.register(Strategy,StrategyAdmin)

class BackTestRunAdmin(admin.ModelAdmin):
    list_display = ('strategy','date','total','commission','rolling_sharpe','draw_down')
    list_filter = ('strategy',)
admin.site.register(BackTestRun,BackTestRunAdmin)

class EquityAdmin(admin.ModelAdmin):
    list_display = ('strategy','name','value','date')
    list_filter = ('strategy','name','date',)
admin.site.register(Equity,EquityAdmin)

