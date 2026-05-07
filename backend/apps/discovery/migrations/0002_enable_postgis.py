from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("discovery", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            "CREATE EXTENSION IF NOT EXISTS postgis;",
            reverse_sql="DROP EXTENSION IF EXISTS postgis;",
        ),
    ]
