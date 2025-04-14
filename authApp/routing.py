from django.urls import path
from PatientBackend.consumers import CallConsumer
from django.urls import re_path

websocket_urlpatterns = [
    re_path(r"ws/call/$", CallConsumer.as_asgi()),
]

