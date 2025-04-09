from django.urls import path
from . import views

app_name = 'okrs'

urlpatterns = [
    path('get_key_results/', views.get_key_results, name='get_key_results'),
] 