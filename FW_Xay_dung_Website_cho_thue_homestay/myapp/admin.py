from django.contrib import admin
from .models import Apartment


@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'address', 'lat', 'lng')
    search_fields = ('name', 'address')


