from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='apartment',
            name='bank_account_name',
            field=models.CharField(blank=True, max_length=150, verbose_name='Chủ tài khoản'),
        ),
        migrations.AddField(
            model_name='apartment',
            name='bank_account_number',
            field=models.CharField(blank=True, max_length=50, verbose_name='Số tài khoản'),
        ),
        migrations.AddField(
            model_name='apartment',
            name='bank_name',
            field=models.CharField(blank=True, max_length=120, verbose_name='Ngân hàng nhận thanh toán'),
        ),
        migrations.AddField(
            model_name='apartment',
            name='payment_note',
            field=models.TextField(blank=True, verbose_name='Ghi chú thanh toán'),
        ),
        migrations.AddField(
            model_name='apartment',
            name='payment_qr',
            field=models.ImageField(blank=True, null=True, upload_to='apartments/payment/', verbose_name='Ảnh mã QR thanh toán'),
        ),
    ]
