from django.urls import path

from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('403/', views.preview_403, name='preview_403'),
    path('404/', views.preview_404, name='preview_404'),
    path('map/', views.map_view, name='map_view'),
    path('apartment/<int:apartment_id>/', views.apartment_detail, name='apartment_detail'),
    path('apartment/<int:apartment_id>/thong-tin/', views.apartment_showcase, name='apartment_showcase'),
    path('api/route/', views.get_route_api, name='api_route'),
    path('api/search/', views.search_region_api, name='api_search'),
    path('api/search-nearby/', views.search_nearby_api, name='api_search_nearby'),
    path('api/geocode-place/', views.geocode_place_api, name='api_geocode_place'),
    path('api/reverse-geocode/', views.reverse_geocode_api, name='api_reverse_geocode'),
]
