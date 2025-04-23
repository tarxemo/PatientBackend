
from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from patient.views import UserListView
from graphene_django.views import GraphQLView
from django.conf import settings
from django.conf.urls.static import static
from .views import *
from authApp.views import TranscribeAndPredictDiseaseView

urlpatterns = [
    path('admin/', admin.site.urls),
    path("graphql/", csrf_exempt(GraphQLView.as_view(graphiql=True))),
    path("api/users/", UserListView.as_view()),
    path("wait_call/", doctor_wait_call, name="call_page"),
    path("emergence_call/", doctor_emergence_call, name="call_page"),
    
    
    # path("import_healthcare_data/", import_healthcare_data),
    # path('import_diseases_and_symptoms/', import_diseases_and_symptoms),
    # path("update_symptoms/", update_symptoms)
    path('api/analyze-symptoms/', TranscribeAndPredictDiseaseView.as_view(), name='analyze-symptoms'),
    path('api/follow-up/', TranscribeAndPredictDiseaseView.as_view(), name='follow-up'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
