import graphene
from graphene import ObjectType, String, Int, Float, Boolean, Date, DateTime, ID, List, Field
# from graphene_django.filter import DjangoFilterConnectionField
from .models import (
    Patient, Doctor, Laboratory, Symptom, Disease, Consultation,
    MedicalTest, PrescribedTest, TestResult, Prescription
)
from .outputs import  *

from graphene_django.filter import DjangoFilterConnectionField





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


# Query definitions
    test_order = graphene.Field(TestOrderType, id=graphene.ID(required=True))
    all_test_orders = graphene.List(TestOrderType)
    test_orders_by_status = graphene.List(
        TestOrderType,
        status=graphene.String(required=False)
    )
    test_orders_by_patient = graphene.List(
        TestOrderType,
        patient_id=graphene.ID(required=True)
    )

    # Resolvers
    def resolve_test_order(self, info, id):
        return TestOrder.objects.get(id=id)

    def resolve_all_test_orders(self, info, **kwargs):
        return TestOrder.objects.all()

    def resolve_test_orders_by_status(self, info, status=None):
        if status:
            return TestOrder.objects.filter(status=status.lower())
        return TestOrder.objects.all()

    def resolve_test_orders_by_patient(self, info, patient_id):
        return TestOrder.objects.filter(patient_id=patient_id)
    
    test_orders = graphene.List(TestOrderType)
    
    def resolve_test_orders(self, info):
        return TestOrder.objects.all()
    
    def resolve_test_order(self, info, id):
        # Use select_related to optimize patient queries
        return TestOrder.objects.select_related('patient').get(id=id)

    def resolve_all_test_orders(self, info):
        # Use select_related to optimize patient queries
        return TestOrder.objects.select_related('patient').all()

# Create schema instance