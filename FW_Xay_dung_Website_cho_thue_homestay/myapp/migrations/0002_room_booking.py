from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('room_name', models.CharField(max_length=100, verbose_name='Tên / số phòng')),
                ('max_people', models.PositiveIntegerField(default=1, verbose_name='Số người tối đa')),
                ('is_available', models.BooleanField(default=True, verbose_name='Phòng còn trống')),
                ('note', models.TextField(blank=True, verbose_name='Ghi chú')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('apartment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rooms', to='myapp.apartment', verbose_name='Căn hộ')),
            ],
            options={
                'verbose_name': 'Phòng',
                'verbose_name_plural': 'Danh sách Phòng',
                'ordering': ['apartment__name', 'room_name'],
                'unique_together': {('apartment', 'room_name')},
            },
        ),
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_name', models.CharField(max_length=150, verbose_name='Họ và tên')),
                ('phone', models.CharField(max_length=20, verbose_name='Số điện thoại')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='Email')),
                ('check_in', models.DateField(verbose_name='Ngày nhận phòng')),
                ('check_out', models.DateField(verbose_name='Ngày trả phòng')),
                ('guests', models.PositiveIntegerField(default=1, verbose_name='Số khách')),
                ('status', models.CharField(choices=[('pending', 'Chờ xác nhận'), ('confirmed', 'Đã xác nhận'), ('checked_in', 'Đang ở'), ('completed', 'Hoàn tất'), ('cancelled', 'Đã hủy')], default='pending', max_length=20, verbose_name='Trạng thái')),
                ('note', models.TextField(blank=True, verbose_name='Ghi chú')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('apartment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to='myapp.apartment', verbose_name='Căn hộ')),
                ('room', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bookings', to='myapp.room', verbose_name='Phòng')),
            ],
            options={
                'verbose_name': 'Đơn đặt phòng',
                'verbose_name_plural': 'Danh sách Đơn đặt phòng',
                'ordering': ['-created_at'],
            },
        ),
    ]
