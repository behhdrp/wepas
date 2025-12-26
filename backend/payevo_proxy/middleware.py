from django.http import HttpResponse

class CORSHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Handle preflight requests
        if request.method == 'OPTIONS':
            response = HttpResponse()
        else:
            response = self.get_response(request)
        
        # Add CORS headers explicitly
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRFToken, X-Requested-With, Accept'
        response['Access-Control-Max-Age'] = '86400'
        response['Access-Control-Expose-Headers'] = 'Content-Type, Authorization'
        
        return response
