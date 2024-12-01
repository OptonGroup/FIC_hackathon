from django.contrib import admin
from django.urls import path, include
from .views import main_page

urlpatterns = [
    path('', main_page, name='main'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('operations/', include('operations.urls')),
] 