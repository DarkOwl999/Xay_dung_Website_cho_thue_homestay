import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from myapp.models import Apartment, ApartmentImage, Service, extract_amount_from_price


CONTENT_MODELS = {
    "myapp.apartment",
    "myapp.apartmentimage",
    "myapp.service",
}


def normalize_price_text(price_text):
    amount = extract_amount_from_price(price_text)
    if amount <= 0:
        return price_text or ""
    return f"{amount:,}".replace(",", ".")


class Command(BaseCommand):
    help = "Import apartment content from a Django-style JSON fixture into this project."

    def add_arguments(self, parser):
        parser.add_argument(
            "json_path",
            nargs="?",
            default="myapp/fixtures/project_content.json",
            help="Path to a fixture-like JSON file. Defaults to myapp/fixtures/project_content.json",
        )

    def handle(self, *args, **options):
        source_path = Path(options["json_path"])
        if not source_path.is_absolute():
            source_path = Path.cwd() / source_path

        if not source_path.exists():
            raise CommandError(f"Missing data file: {source_path}")

        try:
            payload = json.loads(source_path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON file: {exc}") from exc

        if not isinstance(payload, list):
            raise CommandError("The source data must be a JSON array in Django fixture format.")

        created = 0
        updated = 0
        skipped = 0

        for item in payload:
            model_name = item.get("model")
            pk = item.get("pk")
            fields = item.get("fields") or {}

            if model_name not in CONTENT_MODELS:
                skipped += 1
                continue

            if model_name == "myapp.apartment":
                defaults = {
                    "name": fields.get("name", ""),
                    "price": normalize_price_text(fields.get("price", "")),
                    "address": fields.get("address", ""),
                    "desc": fields.get("desc", ""),
                    "image": fields.get("image", ""),
                    "lat": fields.get("lat"),
                    "lng": fields.get("lng"),
                    "bank_name": fields.get("bank_name", ""),
                    "bank_account_name": fields.get("bank_account_name", ""),
                    "bank_account_number": fields.get("bank_account_number", ""),
                    "momo_name": fields.get("momo_name", ""),
                    "momo_phone": fields.get("momo_phone", ""),
                    "payment_note": fields.get("payment_note", ""),
                    "payment_qr": fields.get("payment_qr", ""),
                    "momo_qr": fields.get("momo_qr", ""),
                }
                _, was_created = Apartment.objects.update_or_create(pk=pk, defaults=defaults)
            elif model_name == "myapp.apartmentimage":
                apartment_id = fields.get("apartment")
                if not Apartment.objects.filter(pk=apartment_id).exists():
                    skipped += 1
                    continue

                image_title = fields.get("title", "")
                image_path = fields.get("image", "")
                defaults = {
                    "description": fields.get("description", ""),
                    "display_order": fields.get("display_order", 0),
                }
                _, was_created = ApartmentImage.objects.update_or_create(
                    apartment_id=apartment_id,
                    title=image_title,
                    image=image_path,
                    defaults=defaults,
                )
            else:
                apartment_id = fields.get("apartment")
                if not Apartment.objects.filter(pk=apartment_id).exists():
                    skipped += 1
                    continue

                service_name = fields.get("name", "")
                defaults = {
                    "icon": fields.get("icon", "fa-check-circle"),
                    "description": fields.get("description", ""),
                }
                _, was_created = Service.objects.update_or_create(
                    apartment_id=apartment_id,
                    name=service_name,
                    defaults=defaults,
                )

            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Synced {source_path.name}: created {created}, updated {updated}, skipped {skipped}."
            )
        )
