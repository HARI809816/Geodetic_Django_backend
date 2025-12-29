from django.urls import path
from . import views

urlpatterns = [
    path('stations/<str:date>/', views.get_stations_by_date, name='get_stations_by_date'),
    #path('stations/<str:date>', views.get_stations_by_date),
]