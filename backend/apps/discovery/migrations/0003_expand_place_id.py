from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("discovery", "0002_enable_postgis"),
    ]

    operations = [
        migrations.AlterField(
            model_name="trendlocation",
            name="place_id",
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
