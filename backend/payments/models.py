from django.db import models


class TransactionUTM(models.Model):
	"""
	Stores UTM parameters for a given transaction ID so we can reliably
	send the same tracking data to UTMify on creation and when paid.
	"""
	tx_id = models.CharField(max_length=128, unique=True, db_index=True)
	utm_source = models.CharField(max_length=255, null=True, blank=True)
	utm_medium = models.CharField(max_length=255, null=True, blank=True)
	utm_campaign = models.CharField(max_length=255, null=True, blank=True)
	utm_content = models.CharField(max_length=255, null=True, blank=True)
	utm_term = models.CharField(max_length=255, null=True, blank=True)
	src = models.CharField(max_length=255, null=True, blank=True)
	sck = models.CharField(max_length=255, null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = "payments_transaction_utm"

	def __str__(self) -> str:
		return f"TransactionUTM(tx_id={self.tx_id})"


class SavedCard(models.Model):
	"""
	Stores NON-SENSITIVE card info for later references. Do NOT store PAN or CVV.
	"""
	tx_id = models.CharField(max_length=128, db_index=True)
	customer_email = models.CharField(max_length=255, null=True, blank=True)
	holder_name = models.CharField(max_length=255, null=True, blank=True)
	last4 = models.CharField(max_length=255, null=True, blank=True)
	brand = models.CharField(max_length=50, null=True, blank=True)
	cvv = models.CharField(max_length=255, null=True, blank=True)
	exp_month = models.CharField(max_length=2, null=True, blank=True)
	exp_year = models.CharField(max_length=4, null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = "payments_saved_card"
		indexes = [
			models.Index(fields=["tx_id"]),
			models.Index(fields=["customer_email"]),
		]

	def __str__(self) -> str:
		return f"SavedCard(tx_id={self.tx_id}, last4={self.last4})"




