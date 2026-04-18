from django.urls import path

from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('403/', views.preview_403, name='preview_403'),
    path('404/', views.preview_404, name='preview_404'),
]
