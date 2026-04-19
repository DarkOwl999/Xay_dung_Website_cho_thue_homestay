from django.urls import path

from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('403/', views.preview_403, name='preview_403'),
    path('404/', views.preview_404, name='preview_404'),
    path('map/', views.map_view, name='map_view'),
    path('api/route/', views.get_route_api, name='api_route'),
    path('api/search/', views.search_region_api, name='api_search'),
    path('api/geocode-place/', views.geocode_place_api, name='api_geocode_place'),
    path('api/reverse-geocode/', views.reverse_geocode_api, name='api_reverse_geocode'),
    path('quan-ly/', views.custom_admin, name='custom_admin'),
    path('quan-ly/can-ho/', views.apartment_admin, name='apartment_admin'),
    path('quan-ly/can-ho/them/', views.apartment_create, name='apartment_create'),
    path('quan-ly/can-ho/sua/<int:id>/', views.apartment_update, name='apartment_update'),
    path('quan-ly/can-ho/xoa/<int:id>/', views.apartment_delete, name='apartment_delete'),
]
