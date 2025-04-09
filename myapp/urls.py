from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from .views import home, profile, all_goals, add_result, dashboard_geral
from .views.goals import kr_history

app_name = 'myapp'
urlpatterns = [
    # ex: /myapp/
    path('', home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='myapp/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='myapp:login'), name='logout'),
    path('profile/', profile, name='profile'),
    path('dashboard-geral/', dashboard_geral, name='dashboard_geral'),
    path('all-goals/', all_goals, name='all_goals'),
    path('add-result/<int:okr_id>/', add_result, name='add_result'),
    path('goals/kr/<int:kr_id>/history/', kr_history, name='kr_history'),
]
