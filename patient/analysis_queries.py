from authApp.decorators import login_required_resolver
import graphene
from graphene_django import DjangoObjectType
from django.db.models import Count, Avg
from datetime import datetime, timedelta
from .models import (
    Disease, Patient, Doctor, Consultation, 
    PrescribedTest, Symptom, TestResult, Appointment
)
from authApp.models import CustomUser

class UserType(DjangoObjectType):
    class Meta:
        model = CustomUser
        fields = ('id', 'first_name', 'last_name', 'email')

class PatientType(DjangoObjectType):
    class Meta:
        model = Patient
        fields = "__all__"
        
    age = graphene.Int()
    user = graphene.Field(UserType)
    analytics = graphene.Field(lambda: PatientAnalyticsType)
    
    def resolve_age(self, info):
        return (datetime.now().date() - self.date_of_birth).days // 365
    
    def resolve_user(self, info):
        return self.user
    
    def resolve_analytics(self, info):
        # Calculate consultation stats
        consultations = self.consultations.all()
        consultation_count = consultations.count()
        completed_consultations = consultations.filter(status='Completed').count()
        
        # Calculate test stats
        prescribed_tests = PrescribedTest.objects.filter(consultation__patient=self)
        completed_tests = TestResult.objects.filter(prescribed_test__in=prescribed_tests).count()
        pending_tests = prescribed_tests.count() - completed_tests
        
        # Calculate appointment stats
        now = datetime.now()
        appointments = self.appointments.all()
        upcoming_appointments = appointments.filter(date_time__gt=now).count()
        past_appointments = appointments.filter(date_time__lte=now).count()
        
        # Calculate average consultation duration (placeholder)
        average_consultation_duration = 30
        
        # Get common symptoms
        common_symptoms = (
            Symptom.objects.filter(consultations__patient=self)
            .annotate(count=Count('consultations'))
            .order_by('-count')[:5]
            .values_list('name', flat=True)
        )
        
        # Get frequent diseases
        frequent_diseases = (
            Disease.objects.filter(consultation__patient=self)
            .annotate(count=Count('consultation'))
            .order_by('-count')[:3]
            .values_list('name', flat=True)
        )
        
        return PatientAnalyticsType(
            consultation_count=consultation_count,
            completed_consultations=completed_consultations,
            pending_tests=pending_tests,
            completed_tests=completed_tests,
            upcoming_appointments=upcoming_appointments,
            past_appointments=past_appointments,
            average_consultation_duration=average_consultation_duration,
            common_symptoms=list(common_symptoms),
            frequent_diseases=list(frequent_diseases),
        )

class DoctorType(DjangoObjectType):
    class Meta:
        model = Doctor
        fields = "__all__"
    
    user = graphene.Field(UserType)
    
    def resolve_user(self, info):
        return self.user

class ConsultationType(DjangoObjectType):
    class Meta:
        model = Consultation
        fields = "__all__"

class PrescribedTestType(DjangoObjectType):
    class Meta:
        model = PrescribedTest
        fields = "__all__"

class TestResultType(DjangoObjectType):
    class Meta:
        model = TestResult
        fields = "__all__"

class AppointmentType(DjangoObjectType):
    class Meta:
        model = Appointment
        fields = "__all__"

class PatientAnalyticsType(graphene.ObjectType):
    consultation_count = graphene.Int()
    completed_consultations = graphene.Int()
    pending_tests = graphene.Int()
    completed_tests = graphene.Int()
    upcoming_appointments = graphene.Int()
    past_appointments = graphene.Int()
    average_consultation_duration = graphene.Int()
    common_symptoms = graphene.List(graphene.String)
    frequent_diseases = graphene.List(graphene.String)

class PatientAnalyticsQuery(graphene.ObjectType):
    patient = graphene.Field(PatientType)
    patient_analytics = graphene.Field(PatientAnalyticsType)
    
    @login_required_resolver
    def resolve_patient(self, info):
        # Assuming the logged-in user is a patient
        return Patient.objects.get(user=info.context.user)
    
    @login_required_resolver
    def resolve_patient_analytics(self, info):
        patient = Patient.objects.get(user=info.context.user)
        return patient.analytics