from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from django.conf import settings
from django.http import JsonResponse
from payments.views import serve_frontend

def api_config(request):
	return JsonResponse({"apiBaseUrl": settings.API_BASE_URL})

urlpatterns = [
	path("admin/", admin.site.urls),
	path("api/config/", api_config),
	path("api/", include("payments.urls")),
	path("assets/<path:path>", serve, {"document_root": str(settings.FRONTEND_DIR / "assets")}),
	re_path(r"(.+\.(?:webp|png|jpg|jpeg|svg))$", serve, {"document_root": str(settings.FRONTEND_DIR)}),
	# Serve frontend - catch all for SPA
	re_path(r"^(?!api|admin|assets).*$", serve_frontend, name="frontend"),
]










