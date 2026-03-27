from django.db import models


class Apartment(models.Model):
    name = models.CharField(max_length=200, verbose_name="Tên căn hộ")
    price = models.CharField(max_length=50, verbose_name="Giá tiền (VNĐ)")
    address = models.CharField(max_length=255, verbose_name="Địa chỉ")
    desc = models.TextField(verbose_name="Mô tả", blank=True)
    image = models.ImageField(upload_to='apartments/', verbose_name="Hình ảnh", null=True, blank=True)
    lat = models.FloatField(verbose_name="Vĩ độ (Latitude)")
    lng = models.FloatField(verbose_name="Kinh độ (Longitude)")

    def __str__(self):
        return self.name

    @property
    def total_rooms(self):
        return self.rooms.count()

    @property
    def available_rooms(self):
        return self.rooms.filter(is_available=True).count()

    class Meta:
        verbose_name = "Căn hộ"
        verbose_name_plural = "Danh sách Căn hộ"


class Room(models.Model):
    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.CASCADE,
        related_name='rooms',
        verbose_name="Căn hộ"
    )
    room_name = models.CharField(max_length=100, verbose_name="Tên / số phòng")
    max_people = models.PositiveIntegerField(default=1, verbose_name="Số người tối đa")
    is_available = models.BooleanField(default=True, verbose_name="Phòng còn trống")
    note = models.TextField(blank=True, verbose_name="Ghi chú")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.apartment.name} - {self.room_name}"

    class Meta:
        verbose_name = "Phòng"
        verbose_name_plural = "Danh sách Phòng"
        ordering = ['apartment__name', 'room_name']
        unique_together = ('apartment', 'room_name')


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Chờ xác nhận'),
        ('confirmed', 'Đã xác nhận'),
        ('checked_in', 'Đang ở'),
        ('completed', 'Hoàn tất'),
        ('cancelled', 'Đã hủy'),
    ]

    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name="Căn hộ"
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        related_name='bookings',
        null=True,
        blank=True,
        verbose_name="Phòng"
    )
    customer_name = models.CharField(max_length=150, verbose_name="Họ và tên")
    phone = models.CharField(max_length=20, verbose_name="Số điện thoại")
    email = models.EmailField(blank=True, verbose_name="Email")
    check_in = models.DateField(verbose_name="Ngày nhận phòng")
    check_out = models.DateField(verbose_name="Ngày trả phòng")
    guests = models.PositiveIntegerField(default=1, verbose_name="Số khách")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Trạng thái"
    )
    note = models.TextField(blank=True, verbose_name="Ghi chú")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} - {self.apartment.name}"

    class Meta:
        verbose_name = "Đơn đặt phòng"
        verbose_name_plural = "Danh sách Đơn đặt phòng"
        ordering = ['-created_at']
