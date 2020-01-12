from django.contrib import admin
from API.models import Product, HistoricRate, ProductInfo, DayHistoric, HourHistoric



class ProductAdmin(admin.ModelAdmin):
    list_display = ('currency_pair','base_currency','quote_currency','base_min_size','base_max_size','quote_increment',)
    list_filter = ('currency_pair',)
admin.site.register(Product,ProductAdmin)

class HistoricRateAdmin(admin.ModelAdmin):
    list_display = ('product','date','time','low','high','Open','close','volume')
    list_filter = ('product','date',)
admin.site.register(HistoricRate,HistoricRateAdmin)

class ProductInfoAdmin(admin.ModelAdmin):
    list_display = ('product','date_created','consecutive_missing_avg','consecutive_missing_max','percent_missing','total_days','total_minutes')
    list_filter = ('product',)
admin.site.register(ProductInfo,ProductInfoAdmin)

class DayHistoricAdmin(admin.ModelAdmin):
    list_display = ('product','date','time','low','high','Open','close','volume')
    list_filter = ('product','date',)
admin.site.register(DayHistoric,DayHistoricAdmin)
    
class HourHistoricAdmin(admin.ModelAdmin):
    list_display = ('product','date','low','high','Open','close','volume')
    list_filter = ('product','date',)
admin.site.register(HourHistoric,HourHistoricAdmin)
    