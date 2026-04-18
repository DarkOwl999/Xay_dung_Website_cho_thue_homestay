import re
import uuid

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


def extract_amount_from_price(price_text):
    digits = re.sub(r"\D", "", price_text or "")
    return int(digits) if digits else 0


class Apartment(models.Model):
    name = models.CharField(max_length=200, verbose_name="Tên căn hộ")
    price = models.CharField(max_length=50, verbose_name="Giá tiền (VNĐ)")
    address = models.CharField(max_length=255, verbose_name="Địa chỉ")
    desc = models.TextField(verbose_name="Mô tả", blank=True)
    image = models.ImageField(upload_to="apartments/", verbose_name="Hình ảnh", null=True, blank=True)
    lat = models.FloatField(verbose_name="Vĩ độ (Latitude)")
    lng = models.FloatField(verbose_name="Kinh độ (Longitude)")
    bank_name = models.CharField(max_length=120, blank=True, verbose_name="Ngân hàng nhận thanh toán")
    bank_account_name = models.CharField(max_length=150, blank=True, verbose_name="Chủ tài khoản")
    bank_account_number = models.CharField(max_length=50, blank=True, verbose_name="Số tài khoản")
    momo_name = models.CharField(max_length=150, blank=True, verbose_name="Tên tài khoản MoMo")
    momo_phone = models.CharField(max_length=20, blank=True, verbose_name="Số điện thoại MoMo")
    payment_note = models.TextField(blank=True, verbose_name="Ghi chú thanh toán")
    payment_qr = models.ImageField(
        upload_to="apartments/payment/",
        verbose_name="Ảnh mã QR thanh toán",
        null=True,
        blank=True,
    )
    momo_qr = models.ImageField(
        upload_to="apartments/momo/",
        verbose_name="Ảnh mã QR MoMo",
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.name

    @property
    def price_amount(self):
        return extract_amount_from_price(self.price)

    @property
    def cover_image_url(self):
        if self.image and self.image.name and self.image.storage.exists(self.image.name):
            return self.image.url

        for gallery_image in self.gallery_images.all():
            if (
                gallery_image.image
                and gallery_image.image.name
                and gallery_image.image.storage.exists(gallery_image.image.name)
            ):
                return gallery_image.image.url

        return "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267"

    class Meta:
        verbose_name = "Căn hộ"
        verbose_name_plural = "Danh sách Căn hộ"


class ApartmentImage(models.Model):
    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.CASCADE,
        related_name="gallery_images",
        verbose_name="Căn hộ",
    )
    title = models.CharField(max_length=150, blank=True, verbose_name="Tiêu đề ảnh")
    description = models.CharField(max_length=255, blank=True, verbose_name="Mô tả ngắn")
    image = models.ImageField(upload_to="apartments/gallery/", verbose_name="Ảnh thư viện")
    display_order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự hiển thị")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"Ảnh của {self.apartment.name}"

    class Meta:
        verbose_name = "Ảnh căn hộ"
        verbose_name_plural = "Thư viện ảnh căn hộ"
        ordering = ["display_order", "id"]


class Service(models.Model):
    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.CASCADE,
        related_name="services",
        verbose_name="Căn hộ",
    )
    name = models.CharField(max_length=120, verbose_name="Tên dịch vụ")
    icon = models.CharField(max_length=50, blank=True, default="fa-check-circle", verbose_name="Icon Font Awesome")
    description = models.TextField(blank=True, verbose_name="Mô tả dịch vụ")

    def __str__(self):
        return f"{self.apartment.name} - {self.name}"

    class Meta:
        verbose_name = "Dịch vụ"
        verbose_name_plural = "Dịch vụ căn hộ"
        ordering = ["name"]
        unique_together = ("apartment", "name")


class ApartmentReview(models.Model):
    RATING_CHOICES = [(value, f"{value} sao") for value in range(1, 6)]

    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Căn hộ",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="apartment_reviews",
        verbose_name="Tài khoản",
    )
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, verbose_name="Số sao")
    comment = models.TextField(verbose_name="Bình luận")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    def __str__(self):
        return f"{self.user.username} - {self.apartment.name} ({self.rating} sao)"

    class Meta:
        verbose_name = "Đánh giá căn hộ"
        verbose_name_plural = "Đánh giá căn hộ"
        ordering = ["-updated_at", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["apartment", "user"],
                name="unique_apartment_review_per_user",
            )
        ]


class IntroductionPage(models.Model):
    hero_badge = models.CharField(max_length=80, default="CanHo24h")
    hero_title = models.CharField(max_length=220, default="Không gian thuê căn hộ nghỉ dưỡng chỉn chu và đáng tin cậy")
    hero_description = models.TextField(
        default="Giới thiệu rõ hơn về dịch vụ, trải nghiệm lưu trú và lý do khách hàng chọn CanHo24h cho những kỳ nghỉ ngắn ngày hoặc chuyến công tác dài ngày."
    )
    hero_image = models.ImageField(upload_to="intro/", null=True, blank=True)
    hero_image_secondary = models.ImageField(upload_to="intro/", null=True, blank=True)
    story_title = models.CharField(max_length=180, default="Điều gì khiến CanHo24h khác biệt?")
    story_content = models.TextField(
        blank=True,
        default="<p>CanHo24h tập trung vào trải nghiệm thuê nguyên căn rõ ràng, minh bạch và dễ thao tác. Từ lúc xem căn hộ, kiểm tra lịch trống, đặt cọc đến khi nhận căn, mọi bước đều được tối ưu để khách hàng yên tâm hơn.</p>",
    )
    story_image = models.ImageField(upload_to="intro/", null=True, blank=True)
    feature_one_title = models.CharField(max_length=120, default="Căn hộ chọn lọc")
    feature_one_description = models.TextField(default="Ưu tiên những căn hộ có hình ảnh rõ, thông tin minh bạch và tiện ích phù hợp cho khách nghỉ dưỡng hoặc công tác.")
    feature_two_title = models.CharField(max_length=120, default="Đặt cọc dễ hiểu")
    feature_two_description = models.TextField(default="Khách hàng chỉ thanh toán phần cọc trước, phần còn lại xử lý khi nhận căn để dễ theo dõi và chủ động hơn.")
    feature_three_title = models.CharField(max_length=120, default="Theo dõi bằng GIS")
    feature_three_description = models.TextField(default="Tìm căn hộ theo bản đồ, khu vực, khoảng cách và thời gian di chuyển giúp quyết định thuê nhanh hơn.")
    cta_title = models.CharField(max_length=180, default="Sẵn sàng tìm căn hộ phù hợp cho chuyến đi của bạn?")
    cta_description = models.TextField(default="Khám phá danh sách căn hộ nghỉ dưỡng nổi bật, kiểm tra lịch trống và gửi yêu cầu thuê chỉ trong vài bước.")
    cta_button_text = models.CharField(max_length=80, default="Khám phá căn hộ")
    cta_button_link = models.CharField(max_length=200, default="/map/")
    cta_image = models.ImageField(upload_to="intro/", null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Trang giới thiệu"

    @classmethod
    def get_solo(cls):
        intro_page, _ = cls.objects.get_or_create(pk=1)
        return intro_page

    class Meta:
        verbose_name = "Trang giới thiệu"
        verbose_name_plural = "Trang giới thiệu"


class Booking(models.Model):
    CUSTOMER_CANCELABLE_STATUSES = {"pending", "confirmed"}
    EDITABLE_PAYMENT_STATUSES = {"pending", "failed"}
    DEPOSIT_NIGHT_COUNT = 1

    STATUS_CHOICES = [
        ("pending", "Chờ xác nhận"),
        ("confirmed", "Đã xác nhận"),
        ("checked_in", "Đang ở"),
        ("completed", "Hoàn tất"),
        ("cancelled", "Đã hủy"),
    ]
    PAYMENT_METHOD_CHOICES = [
        ("bank_transfer", "Chuyển khoản"),
        ("momo", "MoMo"),
        ("cash", "Tiền mặt"),
    ]
    PAYMENT_STATUS_CHOICES = [
        ("pending", "Chưa thanh toán"),
        ("paid", "Đã thanh toán"),
        ("failed", "Thanh toán lỗi"),
        ("refunded", "Đã hoàn tiền"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="bookings",
        null=True,
        blank=True,
        verbose_name="Tài khoản",
    )
    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.CASCADE,
        related_name="bookings",
        verbose_name="Căn hộ",
    )
    customer_name = models.CharField(max_length=150, verbose_name="Họ và tên")
    phone = models.CharField(max_length=20, verbose_name="Số điện thoại")
    email = models.EmailField(blank=True, verbose_name="Email")
    check_in = models.DateField(verbose_name="Ngày nhận nhà")
    check_out = models.DateField(verbose_name="Ngày trả nhà")
    guests = models.PositiveIntegerField(default=1, verbose_name="Số khách")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="Trạng thái",
    )
    note = models.TextField(blank=True, verbose_name="Ghi chú")
    access_token = models.UUIDField(default=uuid.uuid4, editable=False, verbose_name="Mã truy cập thanh toán")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="Thời gian thanh toán")
    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES,
        default="bank_transfer",
        verbose_name="Phương thức thanh toán",
    )
    payment_note = models.TextField(blank=True, default="", verbose_name="Ghi chú thanh toán")
    payment_status = models.CharField(
        max_length=30,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending",
        verbose_name="Trạng thái thanh toán",
    )
    nightly_rate = models.BigIntegerField(default=0, verbose_name="Giá mỗi đêm")
    total_amount = models.BigIntegerField(default=0, verbose_name="Tổng tiền")
    transaction_code = models.CharField(max_length=100, blank=True, default="", verbose_name="Mã giao dịch")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} - {self.apartment.name}"

    @property
    def night_count(self):
        if not self.check_in or not self.check_out:
            return 0
        return max((self.check_out - self.check_in).days, 0)

    @property
    def deposit_night_count(self):
        return min(self.night_count, self.DEPOSIT_NIGHT_COUNT)

    @property
    def deposit_amount(self):
        if self.total_amount <= 0:
            return 0
        if self.nightly_rate <= 0:
            return self.total_amount
        return min(self.total_amount, self.nightly_rate * self.deposit_night_count)

    @property
    def remaining_amount(self):
        return max(self.total_amount - self.deposit_amount, 0)

    @property
    def payment_status_display_label(self):
        labels = {
            "pending": "Chưa thanh toán cọc",
            "paid": "Đã thanh toán cọc",
            "failed": "Thanh toán cọc lỗi",
            "refunded": "Đã hoàn cọc",
        }
        return labels.get(self.payment_status, self.get_payment_status_display())

    def build_payment_note(self, payment_method=None):
        deposit_text = (
            f"Thanh toán tiền đặt cọc {self.deposit_amount} VNĐ ngay bây giờ. "
            f"Phần còn lại {self.remaining_amount} VNĐ sẽ thanh toán khi nhận căn."
        )
        method = payment_method or self.payment_method

        if method == "momo":
            method_text = " Bạn có thể thanh toán cọc qua ví MoMo và chờ hệ thống xác nhận."
        else:
            method_text = " Bạn có thể chuyển khoản tiền cọc và chờ hệ thống xác nhận."

        apartment_note = (self.apartment.payment_note or "").strip() if getattr(self, "apartment", None) else ""
        if apartment_note:
            return f"{deposit_text}{method_text} {apartment_note}"
        return f"{deposit_text}{method_text}"

    @property
    def can_customer_cancel(self):
        return self.status in self.CUSTOMER_CANCELABLE_STATUSES and self.payment_status != "paid"

    @property
    def can_update_payment_method(self):
        return self.status not in {"cancelled", "completed"} and self.payment_status in self.EDITABLE_PAYMENT_STATUSES

    def sync_pricing(self, refresh_rate=False):
        if self.apartment_id and (refresh_rate or not self.nightly_rate):
            apartment = getattr(self, "apartment", None)
            if apartment is None:
                apartment = Apartment.objects.only("price").filter(pk=self.apartment_id).first()
            self.nightly_rate = extract_amount_from_price(getattr(apartment, "price", ""))

        self.total_amount = self.nightly_rate * self.night_count

    def save(self, *args, **kwargs):
        refresh_rate = kwargs.pop("refresh_rate", False)
        self.sync_pricing(refresh_rate=refresh_rate)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Đơn thuê căn hộ"
        verbose_name_plural = "Danh sách Đơn thuê căn hộ"
        ordering = ["-created_at"]



class PasswordResetCode(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_reset_codes",
        verbose_name="T?i kho?n",
    )
    email = models.EmailField(verbose_name="Email")
    code = models.CharField(max_length=6, verbose_name="M? x?c nh?n")
    expires_at = models.DateTimeField(verbose_name="H?t h?n l?c")
    used_at = models.DateTimeField(null=True, blank=True, verbose_name="?? d?ng l?c")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ng?y t?o")

    def __str__(self):
        return f"Reset password for {self.user.username} - {self.code}"

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def is_available(self):
        return self.used_at is None and not self.is_expired

    def mark_used(self):
        if self.used_at is None:
            self.used_at = timezone.now()
            self.save(update_fields=["used_at"])

    class Meta:
        verbose_name = "M? qu?n m?t kh?u"
        verbose_name_plural = "M? qu?n m?t kh?u"
        ordering = ["-created_at"]
