"""Root URL configuration for the SARP API."""
from django.contrib import admin

from apps.accounts.views import HealthView
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", HealthView.as_view(), name="health"),
    path("api/v1/auth/", include("apps.accounts.urls")),
]
