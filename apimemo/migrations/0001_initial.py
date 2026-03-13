import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ApiLog",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("method", models.CharField(db_index=True, max_length=10)),
                ("url", models.TextField()),
                ("host", models.CharField(db_index=True, max_length=255)),
                ("path", models.CharField(max_length=2048)),
                ("status_code", models.IntegerField(db_index=True)),
                ("request_headers", models.TextField(blank=True, null=True)),
                ("request_body", models.TextField(blank=True, null=True)),
                ("response_headers", models.TextField(blank=True, null=True)),
                ("response_body", models.TextField(blank=True, null=True)),
                ("duration_ms", models.FloatField(default=0.0)),
                ("error", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                "verbose_name": "API Log",
                "verbose_name_plural": "API Logs",
                "db_table": "api_logs",
                "ordering": ["-created_at"],
            },
        ),
    ]
