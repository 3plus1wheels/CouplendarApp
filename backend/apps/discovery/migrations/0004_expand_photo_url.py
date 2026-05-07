from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("discovery", "0003_expand_place_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="trendlocation",
            name="photo_url",
            field=models.URLField(blank=True, default="", max_length=500),
        ),
    ]
