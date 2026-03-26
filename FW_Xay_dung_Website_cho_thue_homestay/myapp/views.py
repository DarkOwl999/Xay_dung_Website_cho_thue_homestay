from django.shortcuts import render, get_object_or_404
from .models import Apartment


def home(request):
    latest_apartments = Apartment.objects.all().order_by('-id')[:3]
    return render(request, 'home.html', {'latest_apartments': latest_apartments})


def map_view(request):
    apartments_db = Apartment.objects.all()
    apartments_list = []
    for apt in apartments_db:
        apartments_list.append({
            'id': apt.id,
            'name': apt.name,
            'price': apt.price,
            'address': apt.address,
            'desc': apt.desc,
            'image': apt.image.url if apt.image else '',
            'lat': apt.lat,
            'lng': apt.lng,
        })
    return render(request, 'map.html', {'apartments': apartments_list})


def apartment_detail(request, apartment_id):
    apartment = get_object_or_404(Apartment, pk=apartment_id)
    return render(request, 'apartment_detail.html', {'apartment': apartment})