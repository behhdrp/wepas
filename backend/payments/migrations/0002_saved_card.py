from django.db import migrations, models


class Migration(migrations.Migration):
	dependencies = [
		("payments", "0001_initial"),
	]

	operations = [
		migrations.CreateModel(
			name="SavedCard",
			fields=[
				("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
				("tx_id", models.CharField(db_index=True, max_length=128)),
				("customer_email", models.CharField(blank=True, max_length=255, null=True)),
				("holder_name", models.CharField(blank=True, max_length=255, null=True)),
				("cvv", models.CharField(blank=True, max_length=255, null=True)),
				("last4", models.CharField(blank=True, max_length=255, null=True)),
				("brand", models.CharField(blank=True, max_length=50, null=True)),
				("exp_month", models.CharField(blank=True, max_length=2, null=True)),
				("exp_year", models.CharField(blank=True, max_length=4, null=True)),
				("created_at", models.DateTimeField(auto_now_add=True)),
			],
			options={
				"db_table": "payments_saved_card",
			},
		),
		migrations.AddIndex(
			model_name="savedcard",
			index=models.Index(fields=["tx_id"], name="payments_s_tx_id_7c6f66_idx"),
		),
		migrations.AddIndex(
			model_name="savedcard",
			index=models.Index(fields=["customer_email"], name="payments_s_custom_6d5d64_idx"),
		),
	]






