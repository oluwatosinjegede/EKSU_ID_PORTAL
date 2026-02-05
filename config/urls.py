
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from idcards import views as idcard_views

from django.views.generic import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage
from idcards.views import verify_id_card

urlpatterns = [
    path('', include('accounts.urls')),
    path('', include('idcards.urls')),
    path('admin/', admin.site.urls),

    path("verify/<uuid:uid>/", verify_id_card, name="verify-id-card"),
]

    #path(
    #    "favicon.ico",
    #    RedirectView.as_view(
    #        url=staticfiles_storage.url("favicon.ico"),
    #        permanent=True,
    #    ),
    #),
]
   
