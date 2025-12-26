from django.db import migrations, models


class Migration(migrations.Migration):
	initial = True

	dependencies = []

	operations = [
		migrations.CreateModel(
			name="TransactionUTM",
			fields=[
				("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
				("tx_id", models.CharField(db_index=True, max_length=128, unique=True)),
				("utm_source", models.CharField(blank=True, max_length=255, null=True)),
				("utm_medium", models.CharField(blank=True, max_length=255, null=True)),
				("utm_campaign", models.CharField(blank=True, max_length=255, null=True)),
				("utm_content", models.CharField(blank=True, max_length=255, null=True)),
				("utm_term", models.CharField(blank=True, max_length=255, null=True)),
				("src", models.CharField(blank=True, max_length=255, null=True)),
				("sck", models.CharField(blank=True, max_length=255, null=True)),
				("created_at", models.DateTimeField(auto_now_add=True)),
			],
			options={
				"db_table": "payments_transaction_utm",
			},
		),
	]








