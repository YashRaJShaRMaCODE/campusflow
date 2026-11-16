from django.conf import settings


class ProductSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path == "/product/" and response.get("Content-Type", "").startswith("text/html"):
            response["Content-Security-Policy"] = "; ".join((
                "default-src 'self'",
                "base-uri 'self'",
                f"connect-src 'self' {settings.LEADHUB_ORIGIN}".rstrip(),
                "form-action 'self'",
                "frame-ancestors 'none'",
                "object-src 'none'",
                "script-src 'self'",
                "style-src 'self'",
                "upgrade-insecure-requests",
            ))
        return response
