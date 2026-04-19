from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0003_booking_payment_state_sync'),
    ]

    operations = [
        migrations.AddField(
            model_name='apartment',
            name='momo_name',
            field=models.CharField(blank=True, default='', max_length=150, verbose_name='Tên tài khoản MoMo'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='apartment',
            name='momo_phone',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='Số điện thoại MoMo'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='apartment',
            name='momo_qr',
            field=models.ImageField(blank=True, null=True, upload_to='apartments/momo/', verbose_name='Ảnh mã QR MoMo'),
        ),
    ]
