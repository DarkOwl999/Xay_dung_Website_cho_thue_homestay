from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('map/', views.map_view, name='map_view'),
    path('apartment/<int:apartment_id>/', views.apartment_detail, name='apartment_detail'),
    path('api/route/', views.get_route_api, name='api_route'),
    path('api/search/', views.search_region_api, name='api_search'),
]