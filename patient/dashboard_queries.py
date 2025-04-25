from patient.outputs import *
from authApp.decorators import login_required_resolver
import graphene
from graphene_django import DjangoObjectType
from django.db.models import Count, Avg, Q
from datetime import datetime, timedelta, timezone
from .models import (
    Disease, Patient, Doctor, Consultation, 
    PrescribedTest, Symptom, TestResult, Appointment
)
from authApp.models import CustomUser
import graphene
from graphene_django import DjangoObjectType
from .models import (
    CustomUser, Patient, Doctor, Laboratory,
    Symptom, Disease, Consultation,
    MedicalTest, PrescribedTest, TestResult,
    Prescription
)
from django.db.models import Count, Avg, F, ExpressionWrapper, fields
from django.utils import timezone

class UserType(DjangoObjectType):
    class Meta:
        model = CustomUser
        fields = ('id', 'first_name', 'last_name', 'email')

class AppointmentFilterInput(graphene.InputObjectType):
    status = graphene.String()
    upcoming = graphene.Boolean()
    limit = graphene.Int()


class DasboardTestResultType(DjangoObjectType):
    class Meta:
        model = TestResult
        fields = "__all__"
    
    test = graphene.Field(MedicalTestType)
    
    def resolve_test(self, info):
        return self.prescribed_test.test.first()
class TestResultFilterInput(graphene.InputObjectType):
    limit = graphene.Int()

class PatientDashboardType(DjangoObjectType):
    class Meta:
        model = Patient
        fields = "__all__"
        
    age = graphene.Int()
    user = graphene.Field(UserType)
    analytics = graphene.Field(lambda: PatientAnalyticsType)
    appointments = graphene.List(
        lambda: AppointmentType,
        filters=graphene.Argument(AppointmentFilterInput)
    )
    test_results = graphene.List(
        lambda: DasboardTestResultType,
        filters=graphene.Argument(TestResultFilterInput)
    )
    unread_messages_count = graphene.Int()
    can_request_prescription_refill = graphene.Boolean()
    
    def resolve_age(self, info):
        return (datetime.now().date() - self.date_of_birth).days // 365
    
    def resolve_user(self, info):
        return self.user
    
    def resolve_appointments(self, info, filters=None):
        queryset = self.appointments.all()
        
        if filters:
            if filters.get('status'):
                queryset = queryset.filter(status=filters['status'])
            if filters.get('upcoming'):
                now = datetime.now()
                if filters['upcoming']:
                    queryset = queryset.filter(dateTime__gt=now)
                else:
                    queryset = queryset.filter(dateTime__lte=now)
            if filters.get('limit'):
                queryset = queryset[:filters['limit']]
        
        return queryset
    
    def resolve_test_results(self, info, filters=None):
        # Get all test results through prescribed tests and consultations
        prescribed_tests = PrescribedTest.objects.filter(
            consultation__patient=self
        ).prefetch_related('test_result')
        
        test_results = TestResult.objects.filter(
            prescribed_test__in=prescribed_tests
        ).order_by('-uploaded_at')
        
        if filters and filters.get('limit'):
            test_results = test_results[:filters['limit']]
        
        return test_results
    
    def resolve_unread_messages_count(self, info):
        # Placeholder - implement your actual message count logic
        return 2
    
    def resolve_can_request_prescription_refill(self, info):
        # Placeholder - implement your actual refill logic
        return True
    
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
        upcoming_appointments = appointments.filter(dateTime__gt=now).count()
        past_appointments = appointments.filter(dateTime__lte=now).count()
        
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

class AppointmentType(DjangoObjectType):
    class Meta:
        model = Appointment
        fields = "__all__"
    
    doctor = graphene.Field(DoctorType)
    
    def resolve_doctor(self, info):
        return self.doctor


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

class DashboardQuery(graphene.ObjectType):
    patient_home_data = graphene.Field(PatientDashboardType)
    
    @login_required_resolver
    def resolve_patient_home_data(self, info):
        return Patient.objects.get(user__id=info.context.user.id)

    # Basic Model Queries
    medical_tests = graphene.List(MedicalTestType)
    all_patients = graphene.List(PatientOutput)
    all_doctors = graphene.List(DoctorType)
    all_labs = graphene.List(LaboratoryOutput)
    
    # Analytics Queries
    total_users = graphene.Int()
    active_labs = graphene.Int()
    average_response_time = graphene.Float()
    user_distribution = graphene.Field(UserDistributionOutput)
    platform_usage = graphene.List(
        PlatformUsageOutput,
        last_days=graphene.Int(default_value=7)
    )
    recent_activity = graphene.List(
        RecentActivityOutput,
        limit=graphene.Int(default_value=5)
    )

    # Resolvers for Basic Model Queries
    def resolve_medical_tests(self, info):
        return MedicalTest.objects.all()

    def resolve_all_patients(self, info):
        return Patient.objects.all()

    def resolve_all_doctors(self, info):
        return Doctor.objects.all()

    def resolve_all_labs(self, info):
        return Laboratory.objects.all()

    # Resolvers for Analytics Queries
    def resolve_total_users(self, info):
        return CustomUser.objects.count()

    def resolve_active_labs(self, info):
        return Laboratory.objects.all().count()

    def resolve_average_response_time(self, info):
        result = Consultation.objects.annotate(
            response_time=ExpressionWrapper(
                F('updated_at') - F('created_at'),
                output_field=fields.DurationField()
            )
        ).aggregate(avg_response=Avg('response_time'))
        
        if result['avg_response']:
            return round(result['avg_response'].total_seconds() / 3600, 1)
        return 0

    def resolve_user_distribution(self, info):
        return {
            'patient_count': CustomUser.objects.filter(user_type='PATIENT').count(),
            'doctor_count': CustomUser.objects.filter(user_type='DOCTOR').count(),
            'lab_count': CustomUser.objects.filter(user_type='LAB').count(),
            'admin_count': CustomUser.objects.filter(user_type='ADMIN').count(),
        }

    def resolve_platform_usage(self, info, last_days=7):
        end_date = timezone.now()
        start_date = end_date - datetime.timedelta(days=last_days)
        
        consultations = Consultation.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).extra({'date': "date(created_at)"}).values('date').annotate(count=Count('id'))
        
        dates = [start_date + datetime.timedelta(days=x) for x in range(last_days)]
        date_strings = [d.strftime('%Y-%m-%d') for d in dates]
        
        result = []
        for date_str in date_strings:
            day_data = next((c for c in consultations if c['date'] == date_str), None)
            result.append({
                'date': date_str,
                'consultations': day_data['count'] if day_data else 0,
                'prescriptions': 0,  # Add actual prescription count logic
                'test_results': 0,     # Add actual test result count logic
            })
        
        return result

    def resolve_recent_activity(self, info, limit=5):
        recent_users = CustomUser.objects.order_by('-date_joined')[:limit].values(
            'id', 'first_name', 'last_name', 'user_type', 'date_joined'
        )
        
        recent_labs = Laboratory.objects.order_by('-created_at')[:limit].values(
            'id', 'lab_name', 'created_at'
        )
        
        activities = []
        for user in recent_users:
            activities.append({
                'id': f"user_{user['id']}",
                'type': 'user signup',
                'name': f"{user['first_name']} {user['last_name']} ({user['user_type']})",
                'created_at': user['date_joined'],
            })
        
        for lab in recent_labs:
            activities.append({
                'id': f"lab_{lab['id']}",
                'type': 'lab registration',
                'name': lab['lab_name'],
                'created_at': lab['created_at'],
            })
        
        activities.sort(key=lambda x: x['created_at'], reverse=True)
        return activities[:limit]