
from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from django.conf import settings
from django.conf.urls.static import static
# from authApp.views import TranscribeAudioView

urlpatterns = [
    path('admin/', admin.site.urls),
    path("graphql/", csrf_exempt(GraphQLView.as_view(graphiql=True))),
    # path("transcribe/", TranscribeAudioView.as_view(), name="transcribe-audio"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
