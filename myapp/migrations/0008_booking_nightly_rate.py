import re

from django.db import migrations, models


def extract_amount_from_price(price_text):
    digits = re.sub(r"\D", "", price_text or "")
    return int(digits) if digits else 0


def backfill_booking_pricing(apps, schema_editor):
    Booking = apps.get_model("myapp", "Booking")

    for booking in Booking.objects.select_related("apartment").all():
        nightly_rate = extract_amount_from_price(getattr(booking.apartment, "price", ""))
        night_count = 0
        if booking.check_in and booking.check_out:
            night_count = max((booking.check_out - booking.check_in).days, 0)

        booking.nightly_rate = nightly_rate
        booking.total_amount = nightly_rate * night_count
        booking.save(update_fields=["nightly_rate", "total_amount"])


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0007_remove_booking_room_alter_booking_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="nightly_rate",
            field=models.BigIntegerField(default=0, verbose_name="Giá mỗi đêm"),
        ),
        migrations.RunPython(backfill_booking_pricing, migrations.RunPython.noop),
    ]
