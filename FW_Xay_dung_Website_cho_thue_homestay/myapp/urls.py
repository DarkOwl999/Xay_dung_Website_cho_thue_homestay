from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import CustomLoginForm

urlpatterns = [
    path('', views.home, name='home'),
    path('map/', views.map_view, name='map_view'),
    path('apartment/<int:apartment_id>/', views.apartment_detail, name='apartment_detail'),
    path('api/route/', views.get_route_api, name='api_route'),
    path('api/search/', views.search_region_api, name='api_search'),

    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='login.html',
        authentication_form=CustomLoginForm
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),

    path('quan-ly/', views.custom_admin, name='custom_admin'),

    path('quan-ly/can-ho/', views.apartment_admin, name='apartment_admin'),
    path('quan-ly/can-ho/them/', views.apartment_create, name='apartment_create'),
    path('quan-ly/can-ho/sua/<int:id>/', views.apartment_update, name='apartment_update'),
    path('quan-ly/can-ho/xoa/<int:id>/', views.apartment_delete, name='apartment_delete'),

    path('quan-ly/phong/', views.room_admin, name='room_admin'),
    path('quan-ly/phong/them/', views.room_create, name='room_create'),
    path('quan-ly/phong/sua/<int:id>/', views.room_update, name='room_update'),
    path('quan-ly/phong/xoa/<int:id>/', views.room_delete, name='room_delete'),

    path('quan-ly/dat-phong/', views.booking_admin, name='booking_admin'),
    path('quan-ly/dat-phong/sua/<int:id>/', views.booking_update, name='booking_update'),
    path('quan-ly/dat-phong/xoa/<int:id>/', views.booking_delete, name='booking_delete'),

    # Giữ lại các route cũ để tránh vỡ liên kết cũ trong project
    path('quan-ly/them/', views.apartment_create),
    path('quan-ly/sua/<int:id>/', views.apartment_update),
    path('quan-ly/xoa/<int:id>/', views.apartment_delete),
]
