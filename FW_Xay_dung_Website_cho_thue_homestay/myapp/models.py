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

    class Meta:
        verbose_name = "Căn hộ"
        verbose_name_plural = "Danh sách Căn hộ"


