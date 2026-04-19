from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0012_passwordotp"),
    ]

    operations = [
        migrations.AlterField(
            model_name="passwordotp",
            name="purpose",
            field=models.CharField(
                choices=[
                    ("forgot_password", "Quen mat khau"),
                    ("change_password", "Doi mat khau"),
                    ("register_email", "Xac thuc email dang ky"),
                ],
                max_length=30,
                verbose_name="Muc dich",
            ),
        ),
    ]
