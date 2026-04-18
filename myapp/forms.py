import re

from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Apartment, ApartmentReview, Booking, IntroductionPage, PasswordResetCode, Service


# Chỉ các đơn đã được quản trị viên xác nhận mới khóa lịch.
ACTIVE_BOOKING_STATUSES = ("confirmed", "checked_in")

SERVICE_ICON_CHOICES = [
    ("fa-check-circle", "Xác nhận"),
    ("fa-wifi", "Wi-Fi"),
    ("fa-swimming-pool", "Hồ bơi"),
    ("fa-dumbbell", "Phòng gym"),
    ("fa-car", "Bãi đỗ xe"),
    ("fa-motorcycle", "Xe máy"),
    ("fa-utensils", "Bếp / Ăn uống"),
    ("fa-snowflake", "Máy lạnh"),
    ("fa-tv", "TV"),
    ("fa-bath", "Phòng tắm"),
    ("fa-water", "View sông / hồ"),
    ("fa-tree", "Cảnh quan xanh"),
    ("fa-shield-alt", "An ninh"),
    ("fa-concierge-bell", "Lễ tân"),
    ("fa-building", "Tòa nhà"),
    ("fa-paw", "Thú cưng"),
    ("fa-briefcase", "Công tác"),
    ("fa-child", "Gia đình"),
]


class MultipleImageFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.FileField):
    widget = MultipleImageFileInput

    def clean(self, data, initial=None):
        single_file_clean = super().clean

        if not data:
            if self.required:
                raise ValidationError(self.error_messages["required"], code="required")
            return []

        if not isinstance(data, (list, tuple)):
            data = [data]

        return [single_file_clean(item, initial) for item in data]

def _clean_phone_number(value):
    normalized = re.sub(r"[^\d+]", "", (value or "").strip())
    digits_only = re.sub(r"\D", "", normalized)

    if normalized.startswith("+84") and re.fullmatch(r"\+84\d{9}", normalized):
        return normalized

    if digits_only.startswith("84") and len(digits_only) == 11:
        return f"+{digits_only}"

    if re.fullmatch(r"0\d{9,10}", digits_only):
        return digits_only

    raise ValidationError("Số điện thoại chưa đúng định dạng Việt Nam.")


def _has_apartment_booking_conflict(apartment, check_in, check_out, exclude_booking_id=None):
    if not apartment or not check_in or not check_out:
        return False

    conflicts = Booking.objects.filter(
        apartment=apartment,
        status__in=ACTIVE_BOOKING_STATUSES,
        check_in__lt=check_out,
        check_out__gt=check_in,
    )
    if exclude_booking_id:
        conflicts = conflicts.exclude(pk=exclude_booking_id)
    return conflicts.exists()


class ApartmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["desc"].widget = CKEditorUploadingWidget(config_name="apartment_desc")
        self.fields["desc"].help_text = "Bạn có thể chèn ảnh, tiêu đề, bảng và nội dung chi tiết cho căn hộ."

    class Meta:
        model = Apartment
        fields = [
            "name",
            "price",
            "address",
            "desc",
            "image",
            "bank_name",
            "bank_account_name",
            "bank_account_number",
            "momo_name",
            "momo_phone",
            "payment_note",
            "payment_qr",
            "momo_qr",
            "lat",
            "lng",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "price": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control-file"}),
            "bank_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ví dụ: Vietcombank, MB Bank, ACB..."}),
            "bank_account_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Tên người nhận tiền"}),
            "bank_account_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nhập số tài khoản / số ví"}),
            "momo_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Tên tài khoản MoMo nhận tiền"}),
            "momo_phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Số điện thoại MoMo"}),
            "payment_note": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Nội dung chuyển khoản, tiền cọc, lưu ý cho khách..."}),
            "payment_qr": forms.ClearableFileInput(attrs={"class": "form-control-file"}),
            "momo_qr": forms.ClearableFileInput(attrs={"class": "form-control-file"}),
            "lat": forms.NumberInput(attrs={"class": "form-control"}),
            "lng": forms.NumberInput(attrs={"class": "form-control"}),
        }


class ApartmentImageForm(forms.Form):
    title = forms.CharField(
        required=False,
        label="Tiêu đề ảnh",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ví dụ: Phòng khách, ban công, hồ bơi..."}),
    )
    description = forms.CharField(
        required=False,
        label="Mô tả ngắn",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Mô tả ngắn cho nhóm ảnh"}),
    )
    images = MultipleImageField(
        required=True,
        label="Tải ảnh lên",
        widget=MultipleImageFileInput(attrs={"class": "form-control-file", "multiple": True, "accept": "image/*"}),
        help_text="Bạn có thể chọn nhiều ảnh cùng lúc để thêm nhanh vào thư viện.",
    )
    display_order = forms.IntegerField(
        required=False,
        initial=0,
        label="Thứ tự bắt đầu",
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 0}),
    )

    def clean_images(self):
        uploaded_files = self.cleaned_data.get("images") or []
        if not uploaded_files:
            raise ValidationError("Vui lòng chọn ít nhất một ảnh để tải lên.")
        return uploaded_files


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["name", "icon", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ví dụ: Hồ bơi, Wifi, Bãi đỗ xe"}),
            "icon": forms.Select(attrs={"class": "form-control", "data-service-icon-select": "true"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Mô tả chi tiết dịch vụ"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_icon = (self.data.get("icon") or getattr(self.instance, "icon", "") or "fa-check-circle").strip()
        choices = list(SERVICE_ICON_CHOICES)
        choice_values = {value for value, _ in choices}
        if current_icon and current_icon not in choice_values:
            choices.append((current_icon, current_icon))
        self.fields["icon"].choices = choices
        self.fields["icon"].help_text = "Chọn nhanh icon bên dưới hoặc dùng danh sách thả xuống."
        self.initial.setdefault("icon", current_icon or "fa-check-circle")
        self.icon_choices = choices


class IntroductionPageForm(forms.ModelForm):
    class Meta:
        model = IntroductionPage
        fields = [
            "hero_badge",
            "hero_title",
            "hero_description",
            "hero_image",
            "hero_image_secondary",
            "story_title",
            "story_content",
            "story_image",
            "feature_one_title",
            "feature_one_description",
            "feature_two_title",
            "feature_two_description",
            "feature_three_title",
            "feature_three_description",
            "cta_title",
            "cta_description",
            "cta_button_text",
            "cta_button_link",
            "cta_image",
        ]
        labels = {
            "hero_badge": "Nhãn nhỏ đầu trang",
            "hero_title": "Tiêu đề chính",
            "hero_description": "Mô tả mở đầu",
            "hero_image": "Ảnh nổi bật",
            "hero_image_secondary": "Ảnh phụ phần hero",
            "story_title": "Tiêu đề phần giới thiệu",
            "story_content": "Nội dung giới thiệu chi tiết",
            "story_image": "Ảnh minh họa phần giới thiệu",
            "feature_one_title": "Tiêu đề điểm nổi bật 1",
            "feature_one_description": "Mô tả điểm nổi bật 1",
            "feature_two_title": "Tiêu đề điểm nổi bật 2",
            "feature_two_description": "Mô tả điểm nổi bật 2",
            "feature_three_title": "Tiêu đề điểm nổi bật 3",
            "feature_three_description": "Mô tả điểm nổi bật 3",
            "cta_title": "Tiêu đề lời kêu gọi",
            "cta_description": "Mô tả lời kêu gọi",
            "cta_button_text": "Nội dung nút CTA",
            "cta_button_link": "Link nút CTA",
            "cta_image": "Ảnh phụ phần CTA",
        }
        widgets = {
            "hero_badge": forms.TextInput(attrs={"class": "form-control"}),
            "hero_title": forms.TextInput(attrs={"class": "form-control"}),
            "hero_description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "hero_image": forms.ClearableFileInput(attrs={"class": "form-control-file"}),
            "hero_image_secondary": forms.ClearableFileInput(attrs={"class": "form-control-file"}),
            "story_title": forms.TextInput(attrs={"class": "form-control"}),
            "story_image": forms.ClearableFileInput(attrs={"class": "form-control-file"}),
            "feature_one_title": forms.TextInput(attrs={"class": "form-control"}),
            "feature_one_description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "feature_two_title": forms.TextInput(attrs={"class": "form-control"}),
            "feature_two_description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "feature_three_title": forms.TextInput(attrs={"class": "form-control"}),
            "feature_three_description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "cta_title": forms.TextInput(attrs={"class": "form-control"}),
            "cta_description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "cta_button_text": forms.TextInput(attrs={"class": "form-control"}),
            "cta_button_link": forms.TextInput(attrs={"class": "form-control", "placeholder": "/map/ hoặc /"}),
            "cta_image": forms.ClearableFileInput(attrs={"class": "form-control-file"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["story_content"].widget = CKEditorUploadingWidget(config_name="apartment_desc")
        self.fields["story_content"].help_text = "Bạn có thể dùng tiêu đề, ảnh và đoạn nội dung dài để làm trang giới thiệu thu hút hơn."
        self.fields["hero_image_secondary"].help_text = "Ảnh phụ nhỏ để tạo bố cục hero đẹp hơn."
        self.fields["story_image"].help_text = "Ảnh trang trí cho phần nội dung giới thiệu ở giữa trang."
        self.fields["cta_image"].help_text = "Ảnh phụ đặt cạnh khối kêu gọi hành động cuối trang."


class ApartmentReviewForm(forms.ModelForm):
    class Meta:
        model = ApartmentReview
        fields = ["rating", "comment"]
        labels = {
            "rating": "Chọn số sao",
            "comment": "Nội dung đánh giá",
        }
        widgets = {
            "rating": forms.RadioSelect(
                choices=ApartmentReview.RATING_CHOICES,
                attrs={"class": "review-rating-input"},
            ),
            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Chia sẻ cảm nhận của bạn về căn hộ này. Bạn có thể viết ngắn hoặc dài tùy ý.",
                }
            ),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get("rating")
        if rating not in {1, 2, 3, 4, 5}:
            raise ValidationError("Vui lòng chọn số sao từ 1 đến 5.")
        return rating

    def clean_comment(self):
        comment = " ".join((self.cleaned_data.get("comment") or "").split())
        if not comment:
            raise ValidationError("Vui lòng nhập nội dung bình luận.")
        return comment


class ApartmentReviewAdminForm(forms.ModelForm):
    class Meta:
        model = ApartmentReview
        fields = ["apartment", "user", "rating", "comment"]
        labels = {
            "apartment": "Căn hộ",
            "user": "Tài khoản",
            "rating": "Số sao",
            "comment": "Bình luận",
        }
        widgets = {
            "apartment": forms.Select(attrs={"class": "form-control"}),
            "user": forms.Select(attrs={"class": "form-control"}),
            "rating": forms.Select(attrs={"class": "form-control"}),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["apartment"].disabled = True
        self.fields["user"].disabled = True
        self.fields["apartment"].help_text = "Căn hộ gắn với bình luận này được giữ nguyên."
        self.fields["user"].help_text = "Mỗi tài khoản chỉ có 1 đánh giá cho mỗi căn hộ."

    def clean_comment(self):
        comment = " ".join((self.cleaned_data.get("comment") or "").split())
        if not comment:
            raise ValidationError("Vui lòng nhập nội dung bình luận.")
        return comment


class CustomerBookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["customer_name", "phone", "email", "check_in", "check_out", "guests", "note"]
        labels = {
            "customer_name": "Họ và tên",
            "phone": "Số điện thoại",
            "email": "Email xác nhận",
            "check_in": "Ngày nhận nhà",
            "check_out": "Ngày trả nhà",
            "guests": "Số khách",
            "note": "Ghi chú thêm",
        }
        widgets = {
            "customer_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nhập họ và tên"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "09xxxxxxxx"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "example@gmail.com"}),
            "check_in": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "check_out": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "guests": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "note": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Yêu cầu thêm nếu có"}),
        }

    def __init__(self, *args, apartment=None, **kwargs):
        self.apartment = apartment or getattr(kwargs.get("instance"), "apartment", None)
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        self.fields["customer_name"].widget.attrs.update({"maxlength": 150, "autocomplete": "name"})
        self.fields["phone"].widget.attrs.update({"maxlength": 20, "inputmode": "tel", "autocomplete": "tel"})
        self.fields["email"].widget.attrs.update({"autocomplete": "email"})
        self.fields["guests"].widget.attrs.update({"max": 20})

    def clean_customer_name(self):
        customer_name = " ".join((self.cleaned_data.get("customer_name") or "").split())
        if len(customer_name) < 2:
            raise ValidationError("Vui lòng nhập họ tên từ 2 ký tự trở lên.")
        if any(not (char.isalpha() or char.isspace() or char in ".'-") for char in customer_name):
            raise ValidationError("Họ tên chỉ gồm chữ cái, khoảng trắng, dấu chấm hoặc gạch nối.")
        return customer_name

    def clean_phone(self):
        return _clean_phone_number(self.cleaned_data.get("phone"))

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise ValidationError("Vui lòng nhập email để nhận xác nhận đặt thuê.")
        return email

    def clean_guests(self):
        guests = self.cleaned_data.get("guests")
        if guests is None or guests < 1:
            raise ValidationError("Số khách phải lớn hơn 0.")
        if guests > 20:
            raise ValidationError("Vui lòng liên hệ admin nếu đoàn của bạn trên 20 khách.")
        return guests

    def clean(self):
        cleaned_data = super().clean()
        apartment = self.apartment or getattr(self.instance, "apartment", None)
        check_in = cleaned_data.get("check_in")
        check_out = cleaned_data.get("check_out")
        today = timezone.localdate()

        if check_in and check_in < today:
            self.add_error("check_in", "Ngày nhận phòng không được ở trong quá khứ.")

        if check_in and check_out and check_in >= check_out:
            self.add_error("check_out", "Ngày trả phòng phải sau ngày nhận phòng.")

        if _has_apartment_booking_conflict(apartment, check_in, check_out):
            self.add_error("check_in", "Căn hộ này đã có lịch thuê trùng với khoảng thời gian bạn chọn.")

        return cleaned_data


class BookingAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_apartment_id = self.instance.apartment_id
        self.fields["total_amount"].required = False
        self.fields["total_amount"].widget.attrs["readonly"] = True
        self.fields["total_amount"].help_text = "Đây là tổng tiền thuê. Hệ thống hiển thị thu cọc 1 đêm, phần còn lại thanh toán khi nhận căn."
        self.fields["status"].help_text = "Chỉ khi chuyển sang Đã xác nhận hoặc Đang ở thì lịch của căn hộ mới bị khóa với khách khác."
        self.fields["payment_status"].choices = [
            ("pending", "Chưa thanh toán cọc"),
            ("paid", "Đã thanh toán cọc"),
            ("failed", "Thanh toán cọc lỗi"),
            ("refunded", "Đã hoàn cọc"),
        ]

    class Meta:
        model = Booking
        fields = [
            "apartment",
            "customer_name",
            "phone",
            "email",
            "check_in",
            "check_out",
            "guests",
            "status",
            "payment_method",
            "payment_status",
            "total_amount",
            "transaction_code",
            "note",
            "payment_note",
        ]
        widgets = {
            "apartment": forms.Select(attrs={"class": "form-control"}),
            "customer_name": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "check_in": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "check_out": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "guests": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "payment_method": forms.Select(attrs={"class": "form-control"}),
            "payment_status": forms.Select(attrs={"class": "form-control"}),
            "total_amount": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "transaction_code": forms.TextInput(attrs={"class": "form-control"}),
            "note": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "payment_note": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        apartment = cleaned_data.get("apartment") or getattr(self.instance, "apartment", None)
        check_in = cleaned_data.get("check_in")
        check_out = cleaned_data.get("check_out")
        status = cleaned_data.get("status") or getattr(self.instance, "status", "pending")

        if check_in and check_out and check_in >= check_out:
            self.add_error("check_out", "Ngày trả phòng phải sau ngày nhận phòng.")

        if status in ACTIVE_BOOKING_STATUSES and _has_apartment_booking_conflict(
            apartment,
            check_in,
            check_out,
            exclude_booking_id=self.instance.pk,
        ):
            self.add_error("check_in", "Căn hộ này đang có lịch thuê trùng với khoảng thời gian đã chọn.")

        if apartment and check_in and check_out and check_in < check_out:
            apartment_changed = apartment.pk != self._original_apartment_id
            nightly_rate = self.instance.nightly_rate
            if apartment_changed or not nightly_rate:
                nightly_rate = apartment.price_amount

            cleaned_data["nightly_rate"] = nightly_rate
            cleaned_data["total_amount"] = nightly_rate * max((check_out - check_in).days, 0)

        return cleaned_data

    def save(self, commit=True):
        booking = super().save(commit=False)
        booking.nightly_rate = self.cleaned_data.get("nightly_rate", booking.nightly_rate)
        booking.total_amount = self.cleaned_data.get("total_amount", booking.total_amount)

        if commit:
            booking.save()

        return booking


class BookingPaymentMethodForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["payment_method"]
        widgets = {
            "payment_method": forms.RadioSelect(),
        }

    def clean_payment_method(self):
        payment_method = self.cleaned_data.get("payment_method")
        apartment = getattr(self.instance, "apartment", None)

        if not apartment:
            return payment_method

        has_bank_payment = bool(
            apartment.bank_name
            or apartment.bank_account_name
            or apartment.bank_account_number
            or apartment.payment_qr
        )
        has_momo_payment = bool(
            apartment.momo_name
            or apartment.momo_phone
            or apartment.momo_qr
        )

        if payment_method == "bank_transfer" and not has_bank_payment:
            raise ValidationError("Căn hộ này chưa có thông tin chuyển khoản ngân hàng. Vui lòng chọn phương thức khác.")

        if payment_method == "momo" and not has_momo_payment:
            raise ValidationError("Căn hộ này chưa có thông tin thanh toán MoMo. Vui lòng chọn phương thức khác.")

        return payment_method


class CustomRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": "form-control"}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ("email",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        self.fields["username"].widget.attrs.update(
            {"placeholder": "Tên đăng nhập", "autocomplete": "username", "maxlength": 150}
        )
        self.fields["email"].widget.attrs.update(
            {"placeholder": "Email của bạn", "autocomplete": "email"}
        )
        self.fields["password1"].widget.attrs.update(
            {"placeholder": "Mật khẩu", "autocomplete": "new-password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"placeholder": "Nhập lại mật khẩu", "autocomplete": "new-password"}
        )

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if len(username) < 4:
            raise ValidationError("Tên đăng nhập phải từ 4 ký tự trở lên.")
        return username

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Email này đã được sử dụng cho tài khoản khác.")
        return email


class CustomLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        self.fields["username"].widget.attrs.update(
            {"placeholder": "Tên đăng nhập", "autocomplete": "username"}
        )
        self.fields["password"].widget.attrs.update(
            {"placeholder": "Mật khẩu", "autocomplete": "current-password"}
        )


class ForgotPasswordRequestForm(forms.Form):
    email = forms.EmailField(
        label="Email đăng ký",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nhập email bạn đã dùng để đăng ký",
                "autocomplete": "email",
            }
        ),
    )

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if not user:
            raise ValidationError("Email này chưa được đăng ký trong hệ thống.")
        self.user = user
        return email


class ForgotPasswordResetForm(forms.Form):
    email = forms.EmailField(
        label="Email đăng ký",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nhập lại email đã nhận mã",
                "autocomplete": "email",
            }
        ),
    )
    code = forms.CharField(
        label="Mã xác nhận",
        max_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nhập mã 6 số đã gửi về email",
                "autocomplete": "one-time-code",
                "inputmode": "numeric",
                "maxlength": 6,
            }
        ),
    )
    password1 = forms.CharField(
        label="Mật khẩu mới",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nhập mật khẩu mới",
                "autocomplete": "new-password",
            }
        ),
        help_text="Mật khẩu cần đủ mạnh và không nên trùng với thông tin cá nhân.",
    )
    password2 = forms.CharField(
        label="Xác nhận mật khẩu mới",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nhập lại mật khẩu mới",
                "autocomplete": "new-password",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.reset_code = None

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if not user:
            raise ValidationError("Email này chưa được đăng ký trong hệ thống.")
        self.user = user
        return email

    def clean_code(self):
        code = re.sub(r"\D", "", (self.cleaned_data.get("code") or "").strip())
        expected_length = max(int(getattr(settings, "PASSWORD_RESET_CODE_LENGTH", 6)), 4)
        if len(code) != expected_length:
            raise ValidationError(f"Mã xác nhận phải gồm đúng {expected_length} chữ số.")
        return code

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        code = cleaned_data.get("code")
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Mật khẩu xác nhận chưa khớp.")

        if self.user and code:
            reset_code = (
                PasswordResetCode.objects.filter(
                    user=self.user,
                    email__iexact=email,
                    code=code,
                    used_at__isnull=True,
                )
                .order_by("-created_at")
                .first()
            )
            if not reset_code:
                self.add_error("code", "Mã xác nhận không đúng hoặc đã được dùng.")
            elif reset_code.is_expired:
                self.add_error("code", "Mã xác nhận đã hết hạn. Vui lòng yêu cầu mã mới.")
            else:
                self.reset_code = reset_code

        if self.user and password1 and not self.errors.get("password1") and not self.errors.get("password2"):
            try:
                validate_password(password1, user=self.user)
            except ValidationError as exc:
                self.add_error("password1", exc)

        return cleaned_data


class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "is_staff", "is_active"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "is_staff": forms.CheckboxInput(attrs={"class": "admin-toggle-checkbox"}),
            "is_active": forms.CheckboxInput(attrs={"class": "admin-toggle-checkbox"}),
        }
        labels = {
            "username": "Tên đăng nhập",
            "email": "Địa chỉ Email",
            "is_staff": "Cấp quyền Quản trị viên (Admin)",
            "is_active": "Tài khoản đang hoạt động (Bỏ tick để Khóa)",
        }

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if len(username) < 4:
            raise ValidationError("Tên đăng nhập phải từ 4 ký tự trở lên.")
        return username

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            return email

        duplicated_users = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if duplicated_users.exists():
            raise ValidationError("Email này đã được gán cho tài khoản khác.")
        return email

