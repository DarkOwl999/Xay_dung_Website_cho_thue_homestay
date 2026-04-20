import uuid

from django.db import migrations


def sync_booking_payment_columns(apps, schema_editor):
    connection = schema_editor.connection
    table_name = "myapp_booking"

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s
            """,
            [table_name],
        )
        existing_columns = {row[0] for row in cursor.fetchall()}

        statements = []

        if "access_token" not in existing_columns:
            statements.append(f'ALTER TABLE "{table_name}" ADD COLUMN "access_token" uuid')
        if "paid_at" not in existing_columns:
            statements.append(f'ALTER TABLE "{table_name}" ADD COLUMN "paid_at" timestamp with time zone NULL')
        if "payment_method" not in existing_columns:
            statements.append(
                f"""ALTER TABLE "{table_name}" ADD COLUMN "payment_method" varchar(50) NOT NULL DEFAULT 'bank_transfer'"""
            )
        if "payment_note" not in existing_columns:
            statements.append(
                f"""ALTER TABLE "{table_name}" ADD COLUMN "payment_note" text NOT NULL DEFAULT ''"""
            )
        if "payment_status" not in existing_columns:
            statements.append(
                f"""ALTER TABLE "{table_name}" ADD COLUMN "payment_status" varchar(30) NOT NULL DEFAULT 'pending'"""
            )
        if "total_amount" not in existing_columns:
            statements.append(
                f"""ALTER TABLE "{table_name}" ADD COLUMN "total_amount" bigint NOT NULL DEFAULT 0"""
            )
        if "transaction_code" not in existing_columns:
            statements.append(
                f"""ALTER TABLE "{table_name}" ADD COLUMN "transaction_code" varchar(100) NOT NULL DEFAULT ''"""
            )

        for statement in statements:
            cursor.execute(statement)

        cursor.execute(f'SELECT "id" FROM "{table_name}" WHERE "access_token" IS NULL')
        missing_tokens = [row[0] for row in cursor.fetchall()]
        for booking_id in missing_tokens:
            cursor.execute(
                f'UPDATE "{table_name}" SET "access_token" = %s WHERE "id" = %s',
                [str(uuid.uuid4()), booking_id],
            )

        cursor.execute(
            """
            SELECT is_nullable
            FROM information_schema.columns
            WHERE table_name = %s AND column_name = 'access_token'
            """,
            [table_name],
        )
        access_token_meta = cursor.fetchone()
        if access_token_meta and access_token_meta[0] == "YES":
            cursor.execute(f'ALTER TABLE "{table_name}" ALTER COLUMN "access_token" SET NOT NULL')


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0005_alter_booking_payment_method"),
    ]

    operations = [
        migrations.RunPython(sync_booking_payment_columns, migrations.RunPython.noop),
    ]
