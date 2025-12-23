from rest_framework.permissions import BasePermission
from django.conf import settings

class APIKeyCheck(BasePermission):
    message = 'Invalid or missing API Key.'

    def has_permission(self, request, view):
        api_key_sent = request.headers.get('X-API-Key')
        server_key = getattr(settings, 'BUS_API_KEY', None)
        
        if not server_key:
            print("SECURITY WARNING: BUS_API_KEY is not set in settings. Blocking request.")
            return False

        if not api_key_sent:
            return False
        
        return api_key_sent == server_key