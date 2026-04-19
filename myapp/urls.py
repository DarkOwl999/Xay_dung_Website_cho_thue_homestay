from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import CustomLoginForm


urlpatterns = [
    path('', views.home, name='home'),
    path('gioi-thieu/', views.intro_page, name='intro_page'),
    path('403/', views.preview_403, name='preview_403'),
    path('404/', views.preview_404, name='preview_404'),
    path('map/', views.map_view, name='map_view'),
    path('apartment/<int:apartment_id>/', views.apartment_detail, name='apartment_detail'),
    path('apartment/<int:apartment_id>/thong-tin/', views.apartment_showcase, name='apartment_showcase'),
    path('booking/<uuid:access_token>/payment/', views.booking_payment, name='booking_payment'),
    path('booking/<uuid:access_token>/cancel/', views.booking_cancel, name='booking_cancel'),
    path('booking-history/', views.booking_history, name='booking_history'),
    path('api/route/', views.get_route_api, name='api_route'),
    path('api/search/', views.search_region_api, name='api_search'),
    path('api/search-nearby/', views.search_nearby_api, name='api_search_nearby'),
    path('api/geocode-place/', views.geocode_place_api, name='api_geocode_place'),
    path('api/reverse-geocode/', views.reverse_geocode_api, name='api_reverse_geocode'),
    path('register/', views.register, name='register'),
    path('register/xac-thuc-email/', views.register_confirm, name='register_confirm'),
    path('quen-mat-khau/', views.forgot_password_request, name='forgot_password_request'),
    path('quen-mat-khau/xac-nhan/', views.forgot_password_confirm, name='forgot_password_confirm'),
    path('tai-khoan/doi-mat-khau/', views.password_change_request, name='password_change_request'),
    path('tai-khoan/doi-mat-khau/xac-nhan/', views.password_change_confirm, name='password_change_confirm'),
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='login.html',
            authentication_form=CustomLoginForm,
        ),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('quan-ly/', views.custom_admin, name='custom_admin'),
    path('quan-ly/gioi-thieu/', views.intro_page_admin, name='intro_page_admin'),
    path('quan-ly/can-ho/', views.apartment_admin, name='apartment_admin'),
    path('quan-ly/can-ho/them/', views.apartment_create, name='apartment_create'),
    path('quan-ly/can-ho/sua/<int:id>/', views.apartment_update, name='apartment_update'),
    path('quan-ly/can-ho/xoa/<int:id>/', views.apartment_delete, name='apartment_delete'),
    path('quan-ly/can-ho/<int:apartment_id>/noi-dung/', views.apartment_content_admin, name='apartment_content_admin'),
    path('quan-ly/dat-phong/', views.booking_admin, name='booking_admin'),
    path('quan-ly/dat-phong/sua/<int:id>/', views.booking_update, name='booking_update'),
    path('quan-ly/dat-phong/xoa/<int:id>/', views.booking_delete, name='booking_delete'),
    path('quan-ly/danh-gia/', views.review_admin, name='review_admin'),
    path('quan-ly/danh-gia/xoa/<int:id>/', views.review_delete, name='review_delete'),
    path('quan-ly/them/', views.apartment_create),
    path('quan-ly/sua/<int:id>/', views.apartment_update),
    path('quan-ly/xoa/<int:id>/', views.apartment_delete),
    path('quan-ly/tai-khoan/', views.user_admin, name='user_admin'),
    path('quan-ly/tai-khoan/them/', views.user_create, name='user_create'),
    path('quan-ly/tai-khoan/sua/<int:id>/', views.user_update, name='user_update'),
    path('quan-ly/tai-khoan/xoa/<int:id>/', views.user_delete, name='user_delete'),
]
