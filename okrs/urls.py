from django.urls import path
from . import views

app_name = 'okrs'

urlpatterns = [
    path('get_key_results/', views.get_key_results, name='get_key_results'),
    path('api/kpi/<int:kpi_id>/detalhes/', views.get_kpi_detalhes, name='kpi_detalhes'),
] 