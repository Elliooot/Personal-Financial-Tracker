from django.urls import path
from finance import views

app_name = 'rango'
urlpatterns = [
    path('', views.index, name='index'),
    
]