from datetime import datetime, timezone
from authApp.models import CustomUser
import graphene
from graphene import ObjectType, String, Int, Float, Boolean, Date, DateTime, ID, List, Field
# from graphene_django.filter import DjangoFilterConnectionField
from .models import (
    Patient, Doctor, Laboratory, Symptom, Disease, Consultation,
    MedicalTest, PrescribedTest, TestResult, Prescription
)
from .outputs import (
    PatientOutput, DoctorOutput, LaboratoryOutput, SymptomOutput, DiseaseOutput,
    ConsultationOutput, MedicalTestOutput, PrescribedTestOutput, TestResultOutput, PrescriptionOutput
)
from .outputs import *
# Query to fetch a single Patient by ID
class PatientQuery(ObjectType):
    patient = Field(PatientOutput, id=ID(required=True))

    def resolve_patient(self, info, id):
        return Patient.objects.get(id=id)

    # Query to fetch all Patients
    patients = List(PatientOutput)

    def resolve_patients(self, info):
        return Patient.objects.all()

# Query to fetch a single Doctor by ID
    doctor = Field(DoctorOutput, id=ID(required=True))

    def resolve_doctor(self, info, id):
        return Doctor.objects.get(id=id)

# Query to fetch all Doctors
    doctors = List(DoctorOutput)

    def resolve_doctors(self, info):
        return Doctor.objects.all()

# Query to fetch a single Laboratory by ID
    laboratory = Field(LaboratoryOutput, id=ID(required=True))

    def resolve_laboratory(self, info, id):
        return Laboratory.objects.get(id=id)

# Query to fetch all Laboratories
    laboratories = List(LaboratoryOutput)

    def resolve_laboratories(self, info):
        return Laboratory.objects.all()

# Query to fetch a single Symptom by ID
    symptom = Field(SymptomOutput, id=ID(required=True))

    def resolve_symptom(self, info, id):
        return Symptom.objects.get(id=id)

# Query to fetch all Symptoms
    symptoms = List(SymptomOutput)

    def resolve_symptoms(self, info):
        return Symptom.objects.all()

# Query to fetch a single Disease by ID
    disease = Field(DiseaseOutput, id=ID(required=True))

    def resolve_disease(self, info, id):
        return Disease.objects.get(id=id)

# Query to fetch all Diseases
    diseases = List(DiseaseOutput)

    def resolve_diseases(self, info):
        return Disease.objects.all()

# Query to fetch a single Consultation by ID
    consultation = Field(ConsultationOutput, id=ID(required=True))

    def resolve_consultation(self, info, id):
        return Consultation.objects.get(id=id)

# Query to fetch all Consultations
    consultations = List(ConsultationOutput)

    def resolve_consultations(self, info):
        return Consultation.objects.all()

# Query to fetch Consultations by Patient ID
    consultations_by_patient = List(ConsultationOutput, patient_id=ID(required=True))

    def resolve_consultations_by_patient(self, info, patient_id):
        return Consultation.objects.filter(patient_id=patient_id)

# Query to fetch Consultations by Doctor ID
    consultations_by_doctor = List(ConsultationOutput, doctor_id=ID(required=True))

    def resolve_consultations_by_doctor(self, info, doctor_id):
        return Consultation.objects.filter(doctor_id=doctor_id)

# Query to fetch Consultations by Status
    consultations_by_status = List(ConsultationOutput, status=String(required=True))

    def resolve_consultations_by_status(self, info, status):
        return Consultation.objects.filter(status=status)

# Query to fetch a single MedicalTest by ID
    medical_test = Field(MedicalTestOutput, id=ID(required=True))

    def resolve_medical_test(self, info, id):
        return MedicalTest.objects.get(id=id)

# Query to fetch all MedicalTests
    medical_tests = List(MedicalTestOutput)

    def resolve_medical_tests(self, info):
        return MedicalTest.objects.all()
    
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
        return Laboratory.objects.filter(is_active=True).count()

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
# Query to fetch a single PrescribedTest by ID
    prescribed_test = Field(PrescribedTestOutput, id=ID(required=True))

    def resolve_prescribed_test(self, info, id):
        return PrescribedTest.objects.get(id=id)

# Query to fetch all PrescribedTests
    prescribed_tests = List(PrescribedTestOutput)

    def resolve_prescribed_tests(self, info):
        return PrescribedTest.objects.all()

# Query to fetch PrescribedTests by Consultation ID
    prescribed_tests_by_consultation = List(PrescribedTestOutput, consultation_id=ID(required=True))

    def resolve_prescribed_tests_by_consultation(self, info, consultation_id):
        return PrescribedTest.objects.filter(consultation_id=consultation_id)

# Query to fetch a single TestResult by ID
    test_result = Field(TestResultOutput, id=ID(required=True))

    def resolve_test_result(self, info, id):
        return TestResult.objects.get(id=id)

# Query to fetch all TestResults
    test_results = List(TestResultOutput)

    def resolve_test_results(self, info):
        return TestResult.objects.all()

# Query to fetch TestResults by PrescribedTest ID
    test_results_by_prescribed_test = List(TestResultOutput, prescribed_test_id=ID(required=True))

    def resolve_test_results_by_prescribed_test(self, info, prescribed_test_id):
        return TestResult.objects.filter(prescribed_test_id=prescribed_test_id)

# Query to fetch a single Prescription by ID
    prescription = Field(PrescriptionOutput, id=ID(required=True))

    def resolve_prescription(self, info, id):
        return Prescription.objects.get(id=id)

# Query to fetch all Prescriptions
    prescriptions = List(PrescriptionOutput)

    def resolve_prescriptions(self, info):
        return Prescription.objects.all()

# Query to fetch Prescriptions by Consultation ID
    prescriptions_by_consultation = List(PrescriptionOutput, consultation_id=ID(required=True))

    def resolve_prescriptions_by_consultation(self, info, consultation_id):
        return Prescription.objects.filter(consultation_id=consultation_id)
