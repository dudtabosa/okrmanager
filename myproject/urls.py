from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('okrs/', include('okrs.urls', namespace='okrs')),
    path('', include('myapp.urls', namespace='myapp')),
] 