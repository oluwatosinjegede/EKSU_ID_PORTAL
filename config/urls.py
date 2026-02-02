
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from idcards import views as idcard_views

urlpatterns = [
    path('', include('accounts.urls')),
    path('', include('idcards.urls')),
    path('admin/', admin.site.urls),
]

