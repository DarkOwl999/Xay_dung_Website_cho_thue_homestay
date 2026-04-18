import json
import secrets
import string
from datetime import timedelta
from functools import wraps

from django.conf import settings
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from .forms import (
    ACTIVE_BOOKING_STATUSES,
    ApartmentForm,
    ApartmentImageForm,
    ApartmentReviewAdminForm,
    ApartmentReviewForm,
    BookingAdminForm,
    BookingPaymentMethodForm,
    CustomRegisterForm,
    ForgotPasswordRequestForm,
    ForgotPasswordResetForm,
    CustomerBookingForm,
    IntroductionPageForm,
    ServiceForm,
    UserAdminForm,
)
from .models import Apartment, ApartmentImage, ApartmentReview, Booking, IntroductionPage, PasswordResetCode, Service
from .rich_media import render_description_html
from .tool import GISSearchTool, RoutingTool


def _build_transaction_code(apartment_id):
    return f"BK{apartment_id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"


def _booking_history_filter(user):
    return Q(user=user) | (Q(email__iexact=user.email) & ~Q(email=''))


def _build_email_subject(subject):
    return f"CanHo24h | {subject}"


def _send_system_email(subject, template_name, context, recipient):
    if (
        settings.EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend"
        and (not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD)
    ):
        raise RuntimeError(
            "Mailtrap SMTP chưa được cấu hình. Nếu bạn đang dùng Transactional SMTP của Mailtrap, hãy tạo API token rồi điền MAILTRAP_SMTP_USER=api và MAILTRAP_SMTP_PASSWORD=<api_token> vào file .env hoặc mailtrap.env."
        )

    body = render_to_string(template_name, context)
    send_mail(
        _build_email_subject(subject),
        body,
        settings.DEFAULT_FROM_EMAIL,
        [recipient],
        fail_silently=False,
    )


def _generate_password_reset_code():
    code_length = max(int(getattr(settings, "PASSWORD_RESET_CODE_LENGTH", 6)), 4)
    return "".join(secrets.choice(string.digits) for _ in range(code_length))


def _create_password_reset_code(user):
    PasswordResetCode.objects.filter(user=user, used_at__isnull=True).update(used_at=timezone.now())
    return PasswordResetCode.objects.create(
        user=user,
        email=user.email,
        code=_generate_password_reset_code(),
        expires_at=timezone.now() + timedelta(minutes=getattr(settings, "PASSWORD_RESET_CODE_TTL_MINUTES", 10)),
    )


def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapped_view


def custom_403(request, exception=None):
    return render(request, '403.html', status=403)


def custom_404(request, exception=None):
    return render(request, '404.html', status=404)


def preview_403(request):
    return custom_403(request)


def preview_404(request):
    return custom_404(request)


def home(request):
    # Thêm prefetch_related('gallery_images') để lấy sẵn thư viện ảnh
    apartments = Apartment.objects.prefetch_related('gallery_images').order_by('-id')
    paginator = Paginator(apartments, 6)
    apartment_page = paginator.get_page(request.GET.get('page'))
    return render(request, 'home.html', {
        'latest_apartments': apartment_page,
        'apartment_page': apartment_page,
    })


def intro_page(request):
    intro_content = IntroductionPage.get_solo()
    return render(request, 'intro_page.html', {
        'intro_content': intro_content,
        'intro_stats': {
            'apartment_count': Apartment.objects.count(),
            'booking_count': Booking.objects.count(),
            'review_count': ApartmentReview.objects.count(),
        },
        'intro_problem_points': [
            'Thông tin căn hộ thiếu rõ ràng, khó tin tưởng ngay từ lần xem đầu tiên.',
            'Khó kiểm tra lịch trống thật và dễ lo bị đặt trùng ngày nhận căn.',
            'Quy trình đặt cọc, xác nhận và nhận nhà chưa đủ minh bạch.',
            'Không biết căn hộ nằm ở đâu và mất bao lâu để di chuyển.',
        ],
        'intro_solution_points': [
            {
                'icon': 'fas fa-camera-retro',
                'title': intro_content.feature_one_title,
                'description': intro_content.feature_one_description,
            },
            {
                'icon': 'fas fa-file-invoice-dollar',
                'title': intro_content.feature_two_title,
                'description': intro_content.feature_two_description,
            },
            {
                'icon': 'fas fa-map-marked-alt',
                'title': intro_content.feature_three_title,
                'description': intro_content.feature_three_description,
            },
        ],
        'intro_commitments': [
            'Hình ảnh, lịch trống và giá trị thuê được trình bày trực quan, dễ hiểu hơn.',
            'Khách hàng chỉ đặt cọc phần cần thiết và luôn biết rõ phần còn lại thanh toán khi nào.',
            'Tìm kiếm theo bản đồ, khu vực và khoảng cách giúp quyết định thuê nhanh hơn.',
        ],
    })


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


def apartment_detail(request, apartment_id):
    apartment = get_object_or_404(Apartment, pk=apartment_id)
    gallery_images = apartment.gallery_images.all()
    services = apartment.services.all()
    reviews = apartment.reviews.select_related('user').all()
    review_stats = reviews.aggregate(avg_rating=Avg('rating'), review_count=Count('id'))
    average_rating = review_stats['avg_rating'] or 0
    review_count = review_stats['review_count'] or 0
    booked_ranges = []
    description_html = render_description_html(apartment.desc)
    initial_booking_data = {}
    existing_review = None
    selected_review_rating = ""

    active_bookings = apartment.bookings.filter(status__in=ACTIVE_BOOKING_STATUSES).order_by('check_in')
    for booking_item in active_bookings:
        if booking_item.check_in and booking_item.check_out:
            blocked_until = booking_item.check_out - timedelta(days=1)
            if blocked_until >= booking_item.check_in:
                booked_ranges.append({
                    'check_in': booking_item.check_in.isoformat(),
                    'check_out': booking_item.check_out.isoformat(),
                    'blocked_until': blocked_until.isoformat(),
                    'check_in_display': booking_item.check_in.strftime('%d/%m/%Y'),
                    'check_out_display': booking_item.check_out.strftime('%d/%m/%Y'),
                })

    if request.user.is_authenticated:
        full_name = (request.user.get_full_name() or request.user.username).strip()
        initial_booking_data = {
            'customer_name': full_name,
            'email': request.user.email,
        }
        existing_review = apartment.reviews.filter(user=request.user).first()
        if existing_review:
            selected_review_rating = str(existing_review.rating)

    if request.method == 'POST':
        form_type = request.POST.get('form_type', 'booking')
        if form_type == 'review':
            if not request.user.is_authenticated:
                messages.error(request, 'Vui lòng đăng nhập để gửi đánh giá cho căn hộ này.')
                return redirect(f"{reverse('login')}?next={reverse('apartment_detail', args=[apartment.id])}")

            booking_form = CustomerBookingForm(apartment=apartment, initial=initial_booking_data)
            review_form = ApartmentReviewForm(request.POST, instance=existing_review)

            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.apartment = apartment
                review.user = request.user
                was_update = review.pk is not None
                review.save()
                messages.success(
                    request,
                    'Đã cập nhật đánh giá của bạn cho căn hộ.'
                    if was_update
                    else 'Cảm ơn bạn đã gửi đánh giá cho căn hộ.'
                )
                return redirect(f"{reverse('apartment_detail', args=[apartment.id])}#reviews")

            messages.error(request, 'Đánh giá chưa hợp lệ. Vui lòng kiểm tra lại nội dung.')
            return render(request, 'apartment_detail.html', {
                'apartment': apartment,
                'gallery_images': gallery_images,
                'services': services,
                'reviews': reviews,
                'review_form': review_form,
                'selected_review_rating': str(review_form['rating'].value() or ""),
                'review_count': review_count,
                'average_rating': average_rating,
                'average_rating_display': f"{average_rating:.1f}" if review_count else "0.0",
                'star_range': range(1, 6),
                'user_review': existing_review,
                'booked_ranges': booked_ranges,
                'booking_form': booking_form,
                'apartment_description_html': description_html,
            })

        form = CustomerBookingForm(request.POST, apartment=apartment)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.apartment = apartment
            if request.user.is_authenticated:
                booking.user = request.user
            booking.nightly_rate = apartment.price_amount
            booking.sync_pricing()
            booking.payment_method = 'bank_transfer'
            booking.payment_status = 'pending'
            booking.payment_note = booking.build_payment_note('bank_transfer')
            if not booking.transaction_code:
                booking.transaction_code = _build_transaction_code(apartment.id)
            booking.save()
            messages.success(request, 'Đã gửi yêu cầu thuê căn hộ thành công. Quản trị viên sẽ liên hệ với bạn sớm.')
            return redirect('booking_payment', access_token=booking.access_token)
        messages.error(request, 'Biểu mẫu thuê căn hộ chưa hợp lệ. Vui lòng kiểm tra lại.')
    else:
        initial = {}
        if request.user.is_authenticated:
            full_name = (request.user.get_full_name() or request.user.username).strip()
            initial = {
                'customer_name': full_name,
                'email': request.user.email,
            }
        form = CustomerBookingForm(apartment=apartment, initial=initial)

    booking_form = form
    review_form = ApartmentReviewForm(instance=existing_review) if request.user.is_authenticated else ApartmentReviewForm()
    selected_review_rating = str(review_form['rating'].value() or selected_review_rating or "")

    return render(request, 'apartment_detail.html', {
        'apartment': apartment,
        'gallery_images': gallery_images,
        'services': services,
        'reviews': reviews,
        'review_form': review_form,
        'selected_review_rating': selected_review_rating,
        'review_count': review_count,
        'average_rating': average_rating,
        'average_rating_display': f"{average_rating:.1f}" if review_count else "0.0",
        'star_range': range(1, 6),
        'user_review': existing_review,
        'booked_ranges': booked_ranges,
        'booking_form': booking_form,
        'apartment_description_html': description_html,
    })


def booking_payment(request, access_token):
    booking = get_object_or_404(
        Booking.objects.select_related('apartment', 'user'),
        access_token=access_token,
    )
    has_bank_payment = bool(
        booking.apartment.bank_name
        or booking.apartment.bank_account_name
        or booking.apartment.bank_account_number
        or booking.apartment.payment_qr
    )
    has_momo_payment = bool(
        booking.apartment.momo_name
        or booking.apartment.momo_phone
        or booking.apartment.momo_qr
    )

    if request.method == 'POST':
        if not booking.can_update_payment_method:
            messages.error(request, 'Đơn thuê này không thể cập nhật thêm phương thức thanh toán cọc.')
            return redirect('booking_payment', access_token=booking.access_token)

        form = BookingPaymentMethodForm(request.POST, instance=booking)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.payment_note = booking.build_payment_note(booking.payment_method)
            booking.save(update_fields=['payment_method', 'payment_note'])
            messages.success(request, 'Đã cập nhật phương thức thanh toán tiền đặt cọc cho đơn thuê của bạn.')
            return redirect('booking_payment', access_token=booking.access_token)
    else:
        form = BookingPaymentMethodForm(instance=booking)

    selected_payment_method = form['payment_method'].value() or booking.payment_method
    if selected_payment_method == 'bank_transfer' and not has_bank_payment and has_momo_payment:
        selected_payment_method = 'momo'
    elif selected_payment_method == 'momo' and not has_momo_payment and has_bank_payment:
        selected_payment_method = 'bank_transfer'
    elif selected_payment_method not in {'bank_transfer', 'momo'}:
        selected_payment_method = 'bank_transfer' if has_bank_payment else 'momo'

    return render(request, 'booking_payment.html', {
        'booking': booking,
        'payment_form': form,
        'can_update_payment_method': booking.can_update_payment_method,
        'selected_payment_method': selected_payment_method,
        'has_bank_payment': has_bank_payment,
        'has_momo_payment': has_momo_payment,
    })


@login_required
def booking_history(request):
    bookings = Booking.objects.select_related('apartment').filter(
        _booking_history_filter(request.user)
    ).distinct().order_by('-created_at')
    return render(request, 'booking_history.html', {'bookings': bookings})


@login_required
def booking_cancel(request, access_token):
    if request.method != 'POST':
        return redirect('booking_history')

    booking = get_object_or_404(
        Booking.objects.select_related('apartment').filter(_booking_history_filter(request.user)),
        access_token=access_token,
    )

    if not booking.can_customer_cancel:
        messages.error(request, 'Đơn này hiện không thể tự hủy. Nếu cần hỗ trợ thêm, vui lòng liên hệ admin.')
        return redirect('booking_history')

    booking.status = 'cancelled'
    booking.save(update_fields=['status'])
    messages.success(request, f'Đã hủy đơn thuê #{booking.id} thành công.')
    return redirect('booking_history')


def apartment_showcase(request, apartment_id):
    apartment = get_object_or_404(Apartment, pk=apartment_id)
    gallery_images = apartment.gallery_images.all()
    services = apartment.services.all()
    return render(request, 'apartment_showcase.html', {
        'apartment': apartment,
        'gallery_images': gallery_images,
        'services': services,
        'apartment_description_html': render_description_html(apartment.desc),
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


def geocode_place_api(request):
    keyword = request.GET.get('q', '').strip()
    if not keyword:
        return JsonResponse({'error': 'Thiếu từ khóa tìm kiếm'}, status=400)

    try:
        gis_tool = GISSearchTool()
        results = gis_tool.search_locations(keyword)
        return JsonResponse({'results': results})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def reverse_geocode_api(request):
    lat = request.GET.get('lat', '').strip()
    lng = request.GET.get('lng', '').strip()

    if not lat or not lng:
        return JsonResponse({'error': 'Thiếu tọa độ cần tra địa chỉ'}, status=400)

    try:
        lat_value = float(lat)
        lng_value = float(lng)
    except ValueError:
        return JsonResponse({'error': 'Tọa độ không hợp lệ'}, status=400)

    try:
        gis_tool = GISSearchTool()
        result = gis_tool.reverse_geocode(lat_value, lng_value)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def register(request):
    if request.method == 'POST':
        form = CustomRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            try:
                _send_system_email(
                    "Chào mừng bạn đến với CanHo24h",
                    "emails/register_welcome.txt",
                    {
                        "user": user,
                        "login_url": request.build_absolute_uri(reverse("login")),
                        "home_url": request.build_absolute_uri(reverse("home")),
                    },
                    user.email,
                )
                messages.success(request, f"Đăng ký tài khoản thành công. Chúng tôi đã gửi email chào mừng tới {user.email}.")
            except Exception as exc:
                messages.info(
                    request,
                    str(exc)
                    if str(exc)
                    else "Tài khoản đã được tạo thành công, nhưng email chào mừng chưa gửi được."
                )
            login(request, user)
            return redirect('home')
    else:
        form = CustomRegisterForm()
    return render(request, 'register.html', {'form': form})


def forgot_password_request(request):
    initial_email = request.session.get("password_reset_email", "")
    if request.method == "POST":
        form = ForgotPasswordRequestForm(request.POST)
        if form.is_valid():
            user = form.user
            reset_code = _create_password_reset_code(user)
            try:
                _send_system_email(
                    "Mã đặt lại mật khẩu",
                    "emails/password_reset_code.txt",
                    {
                        "user": user,
                        "reset_code": reset_code,
                        "expire_minutes": getattr(settings, "PASSWORD_RESET_CODE_TTL_MINUTES", 10),
                        "reset_url": request.build_absolute_uri(reverse("forgot_password_reset")),
                    },
                    user.email,
                )
            except Exception as exc:
                reset_code.delete()
                messages.error(
                    request,
                    str(exc)
                    if str(exc)
                    else "Hệ thống chưa gửi được email lúc này. Vui lòng kiểm tra cấu hình email rồi thử lại."
                )
            else:
                request.session["password_reset_email"] = user.email
                messages.success(request, f"Mã xác nhận đã được gửi tới {user.email}. Vui lòng kiểm tra hộp thư của bạn.")
                return redirect("forgot_password_reset")
    else:
        form = ForgotPasswordRequestForm(initial={"email": initial_email})
    return render(request, "forgot_password_request.html", {"form": form})


def forgot_password_reset(request):
    initial_email = request.session.get("password_reset_email", "")
    if request.method == "POST":
        form = ForgotPasswordResetForm(request.POST)
        if form.is_valid():
            user = form.user
            reset_code = form.reset_code
            user.set_password(form.cleaned_data["password1"])
            user.save(update_fields=["password"])
            if reset_code:
                reset_code.mark_used()
            request.session.pop("password_reset_email", None)
            messages.success(request, "Mật khẩu đã được cập nhật thành công. Bạn có thể đăng nhập lại ngay bây giờ.")
            return redirect("login")
    else:
        form = ForgotPasswordResetForm(initial={"email": initial_email})
    return render(
        request,
        "forgot_password_reset.html",
        {
            "form": form,
            "request_new_code_url": reverse("forgot_password_request"),
            "expire_minutes": getattr(settings, "PASSWORD_RESET_CODE_TTL_MINUTES", 10),
        },
    )


@admin_required
def custom_admin(request):
    dashboard = {
        'apartment_count': Apartment.objects.count(),
        'service_count': Service.objects.count(),
        'gallery_count': ApartmentImage.objects.count(),
        'booking_count': Booking.objects.count(),
        'pending_booking_count': Booking.objects.filter(status='pending').count(),
        'review_count': ApartmentReview.objects.count(),
        'user_count': User.objects.count(),
    }
    recent_bookings = Booking.objects.select_related('apartment', 'user').order_by('-created_at')[:5]
    latest_apartments = Apartment.objects.order_by('-id')[:5]
    return render(request, 'custom_admin.html', {
        'dashboard': dashboard,
        'recent_bookings': recent_bookings,
        'latest_apartments': latest_apartments,
    })


@admin_required
def intro_page_admin(request):
    intro_content = IntroductionPage.get_solo()
    if request.method == 'POST':
        form = IntroductionPageForm(request.POST, request.FILES, instance=intro_content)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã cập nhật trang giới thiệu.')
            return redirect('intro_page_admin')
    else:
        form = IntroductionPageForm(instance=intro_content)

    return render(request, 'intro_page_form.html', {
        'form': form,
        'intro_content': intro_content,
    })


@admin_required
def apartment_admin(request):
    apartments = Apartment.objects.all().order_by('-id')
    return render(request, 'apartment_admin.html', {'apartments': apartments})


@admin_required
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


@admin_required
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


@admin_required
def apartment_delete(request, id):
    apt = get_object_or_404(Apartment, id=id)
    if request.method == 'POST':
        apt.delete()
        messages.success(request, 'Đã xóa căn hộ.')
    return redirect('apartment_admin')


@admin_required
def apartment_content_admin(request, apartment_id):
    apartment = get_object_or_404(Apartment, id=apartment_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_image':
            image_form = ApartmentImageForm(request.POST, request.FILES)
            service_form = ServiceForm()
            if image_form.is_valid():
                uploaded_files = request.FILES.getlist('images')
                base_title = image_form.cleaned_data.get('title', '').strip()
                description = image_form.cleaned_data.get('description', '').strip()
                display_order = image_form.cleaned_data.get('display_order') or 0

                for index, uploaded_file in enumerate(uploaded_files):
                    item_title = base_title
                    if base_title and len(uploaded_files) > 1:
                        item_title = f'{base_title} {index + 1}'

                    ApartmentImage.objects.create(
                        apartment=apartment,
                        title=item_title,
                        description=description,
                        image=uploaded_file,
                        display_order=display_order + index,
                    )

                messages.success(request, f'Đã thêm {len(uploaded_files)} ảnh mới vào thư viện căn hộ.')
                return redirect('apartment_content_admin', apartment_id=apartment.id)
        elif action == 'add_service':
            image_form = ApartmentImageForm()
            service_form = ServiceForm(request.POST)
            if service_form.is_valid():
                item = service_form.save(commit=False)
                item.apartment = apartment
                item.save()
                messages.success(request, 'Đã thêm dịch vụ mới cho căn hộ.')
                return redirect('apartment_content_admin', apartment_id=apartment.id)
        elif action == 'delete_image':
            ApartmentImage.objects.filter(id=request.POST.get('image_id'), apartment=apartment).delete()
            messages.success(request, 'Đã xóa ảnh khỏi thư viện.')
            return redirect('apartment_content_admin', apartment_id=apartment.id)
        elif action == 'delete_service':
            Service.objects.filter(id=request.POST.get('service_id'), apartment=apartment).delete()
            messages.success(request, 'Đã xóa dịch vụ khỏi căn hộ.')
            return redirect('apartment_content_admin', apartment_id=apartment.id)
        else:
            image_form = ApartmentImageForm()
            service_form = ServiceForm()
    else:
        image_form = ApartmentImageForm()
        service_form = ServiceForm()

    return render(request, 'apartment_content_admin.html', {
        'apartment': apartment,
        'images': apartment.gallery_images.all(),
        'services': apartment.services.all(),
        'image_form': image_form,
        'service_form': service_form,
        'service_icon_choices': getattr(service_form, 'icon_choices', service_form.fields['icon'].choices),
    })


@admin_required
def booking_admin(request):
    bookings = Booking.objects.select_related('apartment', 'user').order_by('-created_at')
    return render(request, 'booking_admin.html', {'bookings': bookings})


@admin_required
def booking_update(request, id):
    booking = get_object_or_404(Booking, id=id)
    if request.method == 'POST':
        form = BookingAdminForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã cập nhật đơn thuê căn hộ.')
            return redirect('booking_admin')
    else:
        form = BookingAdminForm(instance=booking)
    return render(request, 'booking_form.html', {'form': form, 'action': 'Cập nhật', 'booking': booking})


@admin_required
def booking_delete(request, id):
    booking = get_object_or_404(Booking, id=id)
    if request.method == 'POST':
        booking.delete()
        messages.success(request, 'Đã xóa đơn thuê căn hộ.')
    return redirect('booking_admin')


@admin_required
def review_admin(request):
    reviews = ApartmentReview.objects.select_related('apartment', 'user').order_by('-updated_at', '-created_at')
    return render(request, 'review_admin.html', {'reviews': reviews})


@admin_required
def review_update(request, id):
    review = get_object_or_404(ApartmentReview.objects.select_related('apartment', 'user'), id=id)
    if request.method == 'POST':
        form = ApartmentReviewAdminForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã cập nhật bình luận đánh giá.')
            return redirect('review_admin')
    else:
        form = ApartmentReviewAdminForm(instance=review)
    return render(request, 'review_form.html', {'form': form, 'action': 'Cập nhật', 'review': review})


@admin_required
def review_delete(request, id):
    review = get_object_or_404(ApartmentReview, id=id)
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Đã xóa bình luận đánh giá.')
    return redirect('review_admin')


def search_region_api(request):
    keyword = request.GET.get('q', '').strip()
    apartments_db = Apartment.objects.prefetch_related('gallery_images').all()

    if not keyword:
        filtered_apts = apartments_db
    else:
        gis_tool = GISSearchTool()
        filtered_apts = gis_tool.get_apartments_in_region(keyword, apartments_db)

    data_list = _serialize_apartments_for_map(filtered_apts)
    geojson_dict = _build_geojson_payload(data_list, as_dict=True)

    return JsonResponse({'data': data_list, 'geojson': geojson_dict})


def search_nearby_api(request):
    lat = request.GET.get('lat', '').strip()
    lng = request.GET.get('lng', '').strip()
    criteria = request.GET.get('criteria', 'distance').strip()
    value = request.GET.get('value', '5').strip()
    mode = request.GET.get('mode', 'driving').strip()

    if not lat or not lng:
        return JsonResponse({'error': 'Thiếu vị trí hiện tại để tìm kiếm theo bán kính.'}, status=400)

    try:
        lat_value = float(lat)
        lng_value = float(lng)
    except ValueError:
        return JsonResponse({'error': 'Vị trí khách hàng không hợp lệ.'}, status=400)

    apartments_db = Apartment.objects.prefetch_related('gallery_images').all()
    gis_tool = GISSearchTool()
    nearby_payload = gis_tool.get_apartments_near_location(
        lat_value,
        lng_value,
        apartments_db,
        criteria=criteria,
        value=value,
        mode=mode,
    )

    extra_by_id = {}
    filtered_apts = []
    for item in nearby_payload['results']:
        apartment = item['apartment']
        filtered_apts.append(apartment)
        extra_by_id[apartment.id] = {
            'distance_km': item['distance_km'],
            'estimated_time_min': item['estimated_time_min'],
        }

    data_list = _serialize_apartments_for_map(filtered_apts, extra_by_id=extra_by_id)
    geojson_dict = _build_geojson_payload(data_list, as_dict=True)

    if nearby_payload['criteria'] == 'time':
        summary_text = (
            f"Trong khoảng {nearby_payload['value']} phút di chuyển bằng "
            f"{nearby_payload['mode_label']}"
        )
    else:
        summary_text = f"Trong bán kính {nearby_payload['value']} km quanh vị trí của bạn"

    return JsonResponse({
        'data': data_list,
        'geojson': geojson_dict,
        'meta': {
            'criteria': nearby_payload['criteria'],
            'value': nearby_payload['value'],
            'mode': nearby_payload['mode'],
            'mode_label': nearby_payload['mode_label'],
            'search_radius_km': nearby_payload['search_radius_km'],
            'result_count': len(data_list),
            'summary': summary_text,
            'center': {
                'lat': lat_value,
                'lng': lng_value,
            },
        },
    })


@admin_required
def user_admin(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'user_admin.html', {'users': users})


@admin_required
def user_create(request):
    if request.method == 'POST':
        form = CustomRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã tạo tài khoản mới thành công.')
            return redirect('user_admin')
    else:
        form = CustomRegisterForm()
    return render(request, 'user_form.html', {'form': form, 'action': 'Thêm mới'})


@admin_required
def user_update(request, id):
    user_obj = get_object_or_404(User, id=id)
    if request.method == 'POST':
        form = UserAdminForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã cập nhật quyền tài khoản thành công.')
            return redirect('user_admin')
    else:
        form = UserAdminForm(instance=user_obj)
    return render(request, 'user_form.html', {'form': form, 'action': 'Phân quyền'})


@admin_required
def user_delete(request, id):
    user_obj = get_object_or_404(User, id=id)
    if request.method == 'POST':
        if user_obj == request.user:
            messages.error(request, 'LỖI: Bạn không thể tự xóa tài khoản của chính mình!')
        elif user_obj.is_superuser:
            messages.error(request, 'LỖI: Không thể xóa tài khoản Superuser gốc!')
        else:
            user_obj.delete()
            messages.success(request, 'Đã xóa tài khoản thành công.')
    return redirect('user_admin')
