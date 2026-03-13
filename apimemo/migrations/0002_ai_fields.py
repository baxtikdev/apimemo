from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("apimemo", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="apilog",
            name="provider",
            field=models.CharField(blank=True, db_index=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="apilog",
            name="ai_model",
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="apilog",
            name="input_tokens",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="apilog",
            name="output_tokens",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="apilog",
            name="total_tokens",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="apilog",
            name="cost_usd",
            field=models.FloatField(blank=True, null=True),
        ),
    ]
