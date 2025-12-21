from django.utils.deprecation import MiddlewareMixin

class AllowIframeMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        response["X-Frame-Options"] = "ALLOWALL"  # 모든 사이트에서 iframe 허용
        return response