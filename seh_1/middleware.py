from django.contrib import messages
from django.db.models import F
from .models import Component

class ComponentNotificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if any child component has a total value below the limit
        child_components = Component.objects.filter(parent__isnull=False, total__lt=F('notification_limit'))
        if child_components.exists():
            message = f"Child component(s) with total value below the limit: {', '.join(child_components.values_list('title', flat=True))}"
            messages.warning(request, message)

        response = self.get_response(request)
        return response