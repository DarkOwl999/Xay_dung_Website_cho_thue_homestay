from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q
from django.http import JsonResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

from .tool import RoutingTool, GISSearchTool
from .forms import (
    ApartmentForm,
    RoomForm,
    CustomerBookingForm,
    BookingAdminForm,
    CustomRegisterForm,
)
from .models import Apartment, Room, Booking


def home(request):
    latest_apartments = Apartment.objects.all().order_by('-id')[:3]
    return render(request, 'home.html', {'latest_apartments': latest_apartments})


def map_view(request):
    apartments_db = Apartment.objects.all()

    apartments_list = []
    for apt in apartments_db:
        if apt.image:
            img_url = apt.image.url
        else:
            img_url = 'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267'

        apartments_list.append({
            'id': apt.id,
            'name': apt.name,
            'price': apt.price,
            'address': apt.address,
            'desc': apt.desc,
            'image': img_url,
            'lat': apt.lat,
            'lng': apt.lng
        })

    context = {
        'apartments': apartments_list
    }
    return render(request, 'map.html', context)


def apartment_detail(request, apartment_id):
    apartment = get_object_or_404(Apartment, pk=apartment_id)
    rooms = apartment.rooms.all().order_by('room_name')

    if request.method == 'POST':
        form = CustomerBookingForm(request.POST, apartment=apartment)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.apartment = apartment
            booking.save()
            messages.success(request, 'Đã gửi đơn đặt phòng thành công. Quản trị viên sẽ liên hệ với bạn sớm.')
            return redirect('apartment_detail', apartment_id=apartment.id)
        messages.error(request, 'Biểu mẫu đặt phòng chưa hợp lệ. Vui lòng kiểm tra lại.')
    else:
        form = CustomerBookingForm(apartment=apartment)

    return render(request, 'apartment_detail.html', {
        'apartment': apartment,
        'rooms': rooms,
        'booking_form': form,
    })


def get_route_api(request):
    start_lat = request.GET.get('start_lat')
    start_lng = request.GET.get('start_lng')
    end_lat = request.GET.get('end_lat')
    end_lng = request.GET.get('end_lng')
    mode = request.GET.get('mode', 'driving')
    if not all([start_lat, start_lng, end_lat, end_lng]):
        return JsonResponse({'error': 'Thiếu tọa độ đầu vào'}, status=400)
    try:
        tool = RoutingTool()
        result = tool.get_route(start_lat, start_lng, end_lat, end_lng, mode=mode)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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


def is_admin(user):
    return user.is_staff


@login_required
@user_passes_test(is_admin)
def custom_admin(request):
    dashboard = {
        'apartment_count': Apartment.objects.count(),
        'room_count': Room.objects.count(),
        'available_room_count': Room.objects.filter(is_available=True).count(),
        'booking_count': Booking.objects.count(),
        'pending_booking_count': Booking.objects.filter(status='pending').count(),
    }
    recent_bookings = Booking.objects.select_related('apartment', 'room').order_by('-created_at')[:5]
    latest_apartments = Apartment.objects.annotate(total=Count('rooms')).order_by('-id')[:5]
    return render(request, 'custom_admin.html', {
        'dashboard': dashboard,
        'recent_bookings': recent_bookings,
        'latest_apartments': latest_apartments,
    })


@login_required
@user_passes_test(is_admin)
def apartment_admin(request):
    apartments = Apartment.objects.all().order_by('-id')
    return render(request, 'apartment_admin.html', {'apartments': apartments})


@login_required
@user_passes_test(is_admin)
def apartment_create(request):
    if request.method == 'POST':
        form = ApartmentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã thêm căn hộ mới thành công.')
            return redirect('apartment_admin')
    else:
        form = ApartmentForm()
    return render(request, 'apartment_form.html', {'form': form, 'action': 'Thêm mới'})


@login_required
@user_passes_test(is_admin)
def apartment_update(request, id):
    apt = get_object_or_404(Apartment, id=id)
    if request.method == 'POST':
        form = ApartmentForm(request.POST, request.FILES, instance=apt)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã cập nhật căn hộ thành công.')
            return redirect('apartment_admin')
    else:
        form = ApartmentForm(instance=apt)
    return render(request, 'apartment_form.html', {'form': form, 'action': 'Cập nhật'})


@login_required
@user_passes_test(is_admin)
def apartment_delete(request, id):
    apt = get_object_or_404(Apartment, id=id)
    if request.method == 'POST':
        apt.delete()
        messages.success(request, 'Đã xóa căn hộ.')
    return redirect('apartment_admin')


@login_required
@user_passes_test(is_admin)
def room_admin(request):
    rooms = Room.objects.select_related('apartment').order_by('-id')
    return render(request, 'room_admin.html', {'rooms': rooms})


@login_required
@user_passes_test(is_admin)
def room_create(request):
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã thêm phòng mới.')
            return redirect('room_admin')
    else:
        form = RoomForm()
    return render(request, 'room_form.html', {'form': form, 'action': 'Thêm mới'})


@login_required
@user_passes_test(is_admin)
def room_update(request, id):
    room = get_object_or_404(Room, id=id)
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã cập nhật phòng.')
            return redirect('room_admin')
    else:
        form = RoomForm(instance=room)
    return render(request, 'room_form.html', {'form': form, 'action': 'Cập nhật'})


@login_required
@user_passes_test(is_admin)
def room_delete(request, id):
    room = get_object_or_404(Room, id=id)
    if request.method == 'POST':
        room.delete()
        messages.success(request, 'Đã xóa phòng.')
    return redirect('room_admin')


@login_required
@user_passes_test(is_admin)
def booking_admin(request):
    bookings = Booking.objects.select_related('apartment', 'room').order_by('-created_at')
    return render(request, 'booking_admin.html', {'bookings': bookings})


@login_required
@user_passes_test(is_admin)
def booking_update(request, id):
    booking = get_object_or_404(Booking, id=id)
    if request.method == 'POST':
        old_status = booking.status
        old_room_id = booking.room_id
        form = BookingAdminForm(request.POST, instance=booking)
        if form.is_valid():
            updated_booking = form.save()

            if old_room_id and old_room_id != updated_booking.room_id:
                Room.objects.filter(id=old_room_id).update(is_available=True)

            if updated_booking.room:
                if updated_booking.status in ['confirmed', 'checked_in']:
                    updated_booking.room.is_available = False
                    updated_booking.room.save(update_fields=['is_available'])
                elif updated_booking.status in ['completed', 'cancelled']:
                    updated_booking.room.is_available = True
                    updated_booking.room.save(update_fields=['is_available'])
                elif old_status in ['confirmed', 'checked_in'] and updated_booking.status == 'pending':
                    updated_booking.room.is_available = True
                    updated_booking.room.save(update_fields=['is_available'])

            messages.success(request, 'Đã cập nhật đơn đặt phòng.')
            return redirect('booking_admin')
    else:
        form = BookingAdminForm(instance=booking)
    return render(request, 'booking_form.html', {'form': form, 'action': 'Cập nhật', 'booking': booking})


@login_required
@user_passes_test(is_admin)
def booking_delete(request, id):
    booking = get_object_or_404(Booking, id=id)
    room = booking.room
    if request.method == 'POST':
        booking.delete()
        if room and room.bookings.filter(status__in=['confirmed', 'checked_in']).count() == 0:
            room.is_available = True
            room.save(update_fields=['is_available'])
        messages.success(request, 'Đã xóa đơn đặt phòng.')
    return redirect('booking_admin')


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
        img_url = apt.image.url if apt.image else 'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267'
        result.append({
            'id': apt.id,
            'name': apt.name,
            'price': apt.price,
            'address': apt.address,
            'image': img_url,
            'lat': apt.lat,
            'lng': apt.lng
        })

    return JsonResponse({'data': result})

// --- KHOI DAU ---

def _serialize_apartments_for_map(apartments, extra_by_id=None):
    extra_by_id = extra_by_id or {}
    data_list = []

    for apt in apartments:
        item = {
            'id': apt.id,
            'name': apt.name,
            'price': apt.price,
            'address': apt.address,
            'desc': apt.desc,
            'image': apt.cover_image_url,
            'lat': apt.lat,
            'lng': apt.lng,
        }
        item.update(extra_by_id.get(apt.id, {}))
        data_list.append(item)

    return data_list



def _build_geojson_payload(data_list, as_dict=False):
    empty_collection = {"type": "FeatureCollection", "features": []}
    if not data_list:
        return empty_collection if as_dict else json.dumps(empty_collection)

    feature_collection = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    key: value
                    for key, value in item.items()
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [item["lng"], item["lat"]],
                },
            }
            for item in data_list
        ],
    }
    return feature_collection if as_dict else json.dumps(feature_collection, ensure_ascii=False)



def map_view(request):
    apartments_db = Apartment.objects.prefetch_related('gallery_images').all()
    data_list = _serialize_apartments_for_map(apartments_db)
    geojson_data = _build_geojson_payload(data_list)

    context = {
        'apartments': json.dumps(data_list, ensure_ascii=False),
        'geojson_data': geojson_data,
    }
    return render(request, 'map.html', context)
