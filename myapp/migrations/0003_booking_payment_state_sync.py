import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0002_apartment_payment_fields'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name='booking',
                    name='access_token',
                    field=models.UUIDField(default=uuid.uuid4, editable=False, verbose_name='Mã truy cập thanh toán'),
                ),
                migrations.AddField(
                    model_name='booking',
                    name='paid_at',
                    field=models.DateTimeField(blank=True, null=True, verbose_name='Thời gian thanh toán'),
                ),
                migrations.AddField(
                    model_name='booking',
                    name='payment_method',
                    field=models.CharField(choices=[('bank_transfer', 'Chuyển khoản'), ('cash', 'Tiền mặt')], default='bank_transfer', max_length=50, verbose_name='Phương thức thanh toán'),
                ),
                migrations.AddField(
                    model_name='booking',
                    name='payment_note',
                    field=models.TextField(blank=True, default='', verbose_name='Ghi chú thanh toán'),
                ),
                migrations.AddField(
                    model_name='booking',
                    name='payment_status',
                    field=models.CharField(choices=[('pending', 'Chưa thanh toán'), ('paid', 'Đã thanh toán'), ('failed', 'Thanh toán lỗi'), ('refunded', 'Đã hoàn tiền')], default='pending', max_length=30, verbose_name='Trạng thái thanh toán'),
                ),
                migrations.AddField(
                    model_name='booking',
                    name='total_amount',
                    field=models.BigIntegerField(default=0, verbose_name='Tổng tiền'),
                ),
                migrations.AddField(
                    model_name='booking',
                    name='transaction_code',
                    field=models.CharField(blank=True, default='', max_length=100, verbose_name='Mã giao dịch'),
                ),
            ],
        ),
    ]
