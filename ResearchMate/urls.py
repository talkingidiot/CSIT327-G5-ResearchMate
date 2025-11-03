"""
URL configuration for ResearchMate project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),

    # Include your app URLs
    path('', include('ConsultApp.urls')),  # all app URLs, e.g., login, dashboards, consultant_market_add

    # Optional: redirect root URL to login (if you want / to go to login)
    path('', RedirectView.as_view(url='/home/', permanent=False)),
]
