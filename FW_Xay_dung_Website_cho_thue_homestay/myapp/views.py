from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth import login

from .models import Apartment
from .tool import RoutingTool, GISSearchTool
from .forms import CustomRegisterForm


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
            'image': apt.image.url if apt.image else 'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267',
            'lat': apt.lat,
            'lng': apt.lng,
        })
    return render(request, 'map.html', {'apartments': apartments_list})


def apartment_detail(request, apartment_id):
    apartment = get_object_or_404(Apartment, pk=apartment_id)
    rooms = apartment.rooms.all().order_by('room_name')
    return render(request, 'apartment_detail.html', {'apartment': apartment, 'rooms': rooms})


def get_route_api(request):
    start_lat = request.GET.get('start_lat')
    start_lng = request.GET.get('start_lng')
    end_lat = request.GET.get('end_lat')
    end_lng = request.GET.get('end_lng')
    mode = request.GET.get('mode', 'driving')

    if not all([start_lat, start_lng, end_lat, end_lng]):
        return JsonResponse({'error': 'Thiếu tọa độ đầu vào'}, status=400)

    tool = RoutingTool()
    result = tool.get_route(start_lat, start_lng, end_lat, end_lng, mode=mode)
    return JsonResponse(result)


def search_region_api(request):
    keyword = request.GET.get('q', '').strip()
    apartments_db = Apartment.objects.all()

    if not keyword:
        filtered_apts = apartments_db
    else:
        gis_tool = GISSearchTool()
        filtered_apts = gis_tool.get_apartments_in_region(keyword, apartments_db)

    result = []
    for apt in filtered_apts:
        result.append({
            'id': apt.id,
            'name': apt.name,
            'price': apt.price,
            'address': apt.address,
            'image': apt.image.url if apt.image else 'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267',
            'lat': apt.lat,
            'lng': apt.lng,
        })
    return JsonResponse({'data': result})


def register(request):
    if request.method == 'POST':
        form = CustomRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomRegisterForm()
    return render(request, 'register.html', {'form': form})
