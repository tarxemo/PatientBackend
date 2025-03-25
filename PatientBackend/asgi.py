import os
import django

# Set the settings module before doing anything else
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PatientBackend.settings')

# Explicitly initialize Django
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from authApp.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
