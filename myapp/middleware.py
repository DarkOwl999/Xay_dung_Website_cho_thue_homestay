from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import render


class FriendlyErrorPagesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except PermissionDenied:
            if self._should_render_custom_page(request, 403):
                return render(request, "403.html", status=403)
            raise
        except Http404:
            if self._should_render_custom_page(request, 404):
                return render(request, "404.html", status=404)
            raise

        if self._should_render_custom_page(request, response.status_code):
            template_name = "403.html" if response.status_code == 403 else "404.html"
            return render(request, template_name, status=response.status_code)

        return response

    def _should_render_custom_page(self, request, status_code):
        if status_code not in {403, 404}:
            return False

        if request.path.startswith("/api/") or request.path.startswith("/media/") or request.path.startswith("/static/"):
            return False

        accepted_content = request.headers.get("Accept", "")
        if accepted_content and "text/html" not in accepted_content and "*/*" not in accepted_content:
            return False

        return True
