from django.urls import path
from PatientBackend.consumers import CallConsumer

websocket_urlpatterns = [
    path("ws/call/<int:user_id>/", CallConsumer.as_asgi()),
]
