from django.urls import path
from .views import create_pix_transaction, korepay_postback, transaction_status

urlpatterns = [
	path("transactions/pix/", create_pix_transaction, name="create_pix_transaction"),
	path("postbacks/korepay/", korepay_postback, name="korepay_postback"),
	path("transactions/status/", transaction_status, name="transaction_status"),
]


