import graphene
from graphene import ObjectType, String, Int, Float, Boolean, Date, DateTime, ID, List, Field
from graphql import GraphQLError

from authApp.decorators import login_required_resolver
# from graphene_django.filter import DjangoFilterConnectionField
from .models import (
    Appointment, Patient, Doctor, Laboratory, Symptom, Disease, Consultation,
    MedicalTest, PrescribedTest, TestResult, Prescription
)
from .outputs import  *
from graphql_jwt.decorators import login_required

# from graphene_django.filter import DjangoFilterConnectionField





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

    @login_required_resolver
    def resolve_doctors(self, info):
        if info.context.user.user_type == "patient":
            return Doctor.objects.all()
        else:
            return Patient.objects.all()

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

 


    consultations_by_me = graphene.List(ConsultationOutput)

    @login_required_resolver
    def resolve_consultations(self, info):
        user = info.context.user
        if user.user_type == "patient":
            return Consultation.objects.filter(patient__user=user)
        if user.user_type == "doctor":
            return Consultation.objects.filter(doctor__user=user)
        return Consultation.objects.all()
    def resolve_consultations_by_me(self, info):
        user = info.context.user
        if user.user_type == "doctor":
            return Consultation.objects.filter(doctor__user=user)
        else:
            return Consultation.objects.filter(patient__user=user)


# Query to fetch a single MedicalTest by ID
    medical_test = Field(MedicalTestOutput, id=ID(required=True))

    def resolve_medical_test(self, info, id):
        return MedicalTest.objects.get(id=id)

# Query to fetch all MedicalTests
    medical_tests = List(MedicalTestOutput)

    def resolve_medical_tests(self, info):
        return MedicalTest.objects.all()

 

 



    test_results_by_me = graphene.List(TestResultOutput)

    @login_required_resolver
    def resolve_test_results_by_me(self, info):
        user = info.context.user

        if hasattr(user, "doctor"):
            return TestResult.objects.select_related(
                "test_order__doctor__user"
            ).filter(test_order__doctor__user=user)

        elif hasattr(user, "patient"):
            return TestResult.objects.select_related(
                "test_order__patient__user"
            ).filter(test_order__patient__user=user)

        elif hasattr(user, "labtech"):
            return TestResult.objects.select_related(
                "laboratory__lab_tech__user"
            ).filter(laboratory__lab_tech__user=user)

        raise GraphQLError("Access denied: Only the doctor, patient, or lab tech involved can view these test results.")


# Query to fetch all TestResults
    all_test_results = List(TestResultOutput)

    @login_required_resolver
    def resolve_all_test_results(self, info):
        user = info.context.user
        if user.user_type == "patient":
            return TestResult.objects.filter(test_order__patient__user = user)
        if user.user_type == "doctor":
            return TestResult.objects.all()
        else:
            return TestResult.objects.all()




# Query to fetch medical tests 

    all_medical_tests = graphene.List(MedicalTestType)
    medical_test = graphene.Field(MedicalTestType, id=graphene.ID(required=True))

    def resolve_all_medical_tests(self, info):
        return MedicalTest.objects.all()

    def resolve_medical_test(self, info, id):
        try:
            return MedicalTest.objects.get(pk=id)
        except MedicalTest.DoesNotExist:
            return None
        
        
    test_order = graphene.Field(TestOrderOutput, id=graphene.ID(required=True))

    def resolve_test_order(self, info, id):
        return TestOrder.objects.get(id=id)





# Query for fetching appointments
    all_appointments = graphene.List(AppointmentOutput)
    appointment_by_id = graphene.Field(AppointmentOutput, id=graphene.ID(required=True))

    def resolve_all_appointments(self, info):
        return Appointment.objects.all()

    def resolve_appointment_by_id(self, info, id):
        try:
            return Appointment.objects.get(id=id)
        except Appointment.DoesNotExist:
            return None

 

    prescription_by_user = graphene.List(PrescriptionOutput)
    
    @login_required_resolver
    def resolve_prescription_by_user(self, info):
        user = info.context.user

        if user.user_type == "doctor":
            return  Prescription.objects.filter(doctor__user=user)

        else:
            return Prescription.objects.filter(consultation__patient__user=user)

    @login_required_resolver
    def resolve_prescriptions(self, info):
        user = info.context.user
        if user.user_type == "patient":
            return Prescription.objects.filter(test_result__patient__user=user)
            
        return Prescription.objects.all()

# Query to fetch Prescriptions by Consultation ID
    prescriptions_by_consultation = List(PrescriptionOutput, consultation_id=ID(required=True))

    def resolve_prescriptions_by_consultation(self, info, consultation_id):
        return Prescription.objects.filter(consultation_id=consultation_id)


   
  

#new

 

    all_doctors = graphene.List(DoctorType)
    doctor = graphene.Field(DoctorType, id=graphene.ID(required=True))
    all_labtechs = graphene.List(LabTechType)
    labtech = graphene.Field(LabTechType, id=graphene.ID(required=True))
    all_laboratories = graphene.List(LaboratoryType)
    laboratory = graphene.Field(LaboratoryType, id=graphene.ID(required=True))

 

    def resolve_all_doctors(self, info):
        return Doctor.objects.all()

    def resolve_doctor(self, info, id):
        return Doctor.objects.get(pk=id)

    def resolve_all_labtechs(self, info):
        return LabTech.objects.all()

    def resolve_labtech(self, info, id):
        return LabTech.objects.get(pk=id)

    def resolve_all_laboratories(self, info):
        return Laboratory.objects.all()

    def resolve_laboratory(self, info, id):
        return Laboratory.objects.get(pk=id)


 
    test_orders_by_me = graphene.List(TestOrderType)

    @login_required_resolver
    def resolve_test_orders_by_me(self, info):
        user = info.context.user

        if hasattr(user, "doctor"):
            return TestOrder.objects.select_related("patient__user")\
                .filter(doctor__user=user)

        elif hasattr(user, "patient"):
            return TestOrder.objects.select_related("patient__user")\
                .filter(patient__user=user)

    def resolve_test_orders_by_patient(self, info, patient_id):
        return TestOrder.objects.filter(patient_id=patient_id)
    
    test_orders = graphene.List(TestOrderType)
    
    @login_required_resolver
    def resolve_test_orders(self, info):
        if info.context.user.user_type == 'patient':
            return TestOrder.objects.filter(patient__user = info.context.user)
        return TestOrder.objects.all()
    
    def resolve_test_order(self, info, id):
        # Use select_related to optimize patient queries
        return TestOrder.objects.select_related('patient').get(id=id)

    def resolve_all_test_orders(self, info):
        # Use select_related to optimize patient queries
        return TestOrder.objects.select_related('patient').all()

# Create schema instance
