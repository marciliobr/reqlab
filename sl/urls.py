from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', include('lab.urls')),
    path('', include('social_django.urls'), name='social'),
]
