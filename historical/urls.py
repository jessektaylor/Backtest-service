from django.urls import path
from . import views

app_name = 'historical'

urlpatterns = [
    path('test/', views.test),
    path('portfolioview',views.PortfolioView.as_view(),name='portfolio-view'),
    ]