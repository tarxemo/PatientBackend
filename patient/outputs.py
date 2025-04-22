import graphene
from graphene import ObjectType, String, Int, Float, Boolean, Date, DateTime, ID, List, Field
from graphene_django.types import DjangoObjectType
from .models import (
    Patient, Doctor, Laboratory, Symptom, Disease, Consultation,
    MedicalTest, PrescribedTest, TestOrder, TestResult, Prescription
)
from authApp.outputs import CustomUserOutput
# Output for BaseProfile (abstract model)
class BaseProfileOutput(ObjectType):
    phone_number = String()
    address = String()

# Output for Patient
# output.py
class PatientOutput(BaseProfileOutput):
    id = ID()
    date_of_birth = Date()
    gender = String()
    medical_history = String()
    user = Field(lambda: CustomUserOutput)

    def resolve_user(self, info):
        return self.user
# Output for Doctor
class DoctorOutput(BaseProfileOutput):
    id = ID()
    specialization = String()
    license_number = String()
    years_of_experience = Int()
    is_available = Boolean()
    user = Field(lambda: CustomUserOutput)

    def resolve_user(self, info):
        return self.user

# Output for Laboratory
class LaboratoryOutput(BaseProfileOutput):
    id = ID()
    lab_name = String()
    accreditation_number = String()
    location = String()
    user = Field(lambda: CustomUserOutput)
    created_at=Date()
    def resolve_user(self, info):
        return self.user

# Output for Symptom
class SymptomOutput(DjangoObjectType):
    class Meta:
        model = Symptom
        fields = ("id", "name", "description")

# Output for Disease
class DiseaseOutput(DjangoObjectType):
    related_symptoms = List(SymptomOutput)

    class Meta:
        model = Disease
        fields = ("id", "name", "description", "related_symptoms")

    def resolve_related_symptoms(self, info):
        return self.related_symptoms.all()

# Output for Consultation
class ConsultationOutput(DjangoObjectType):
    patient = Field(PatientOutput)
    doctor = Field(DoctorOutput)
    symptoms = List(SymptomOutput)
    disease = Field(DiseaseOutput)

    class Meta:
        model = Consultation
        fields = ("id", "patient", "doctor", "symptoms", "disease", "status", "created_at", "updated_at")

    def resolve_patient(self, info):
        return self.patient

    def resolve_doctor(self, info):
        return self.doctor

    def resolve_symptoms(self, info):
        return self.symptoms.all()

    def resolve_disease(self, info):
        return self.disease

# Output for MedicalTest
class MedicalTestOutput(DjangoObjectType):
    class Meta:
        model = MedicalTest
        fields = ("id", "name", "description")

# Output for PrescribedTest
class PrescribedTestOutput(DjangoObjectType):
    consultation = Field(ConsultationOutput)
    test = Field(MedicalTestOutput)

    class Meta:
        model = PrescribedTest
        fields = ("id", "consultation", "test", "notes")

    def resolve_consultation(self, info):
        return self.consultation

    def resolve_test(self, info):
        return self.test

# Output for TestResult
class TestResultOutput(DjangoObjectType):
    prescribed_test = Field(PrescribedTestOutput)
    laboratory = Field(LaboratoryOutput)

    class Meta:
        model = TestResult
        fields = ("id", "prescribed_test", "laboratory", "result_file", "notes", "uploaded_at")

    def resolve_prescribed_test(self, info):
        return self.prescribed_test

    def resolve_laboratory(self, info):
        return self.laboratory

# Output for Prescription
class PrescriptionOutput(DjangoObjectType):
    consultation = Field(ConsultationOutput)

    class Meta:
        model = Prescription
        fields = ("id", "consultation", "dosage", "instructions", "prescribed_at")

    def resolve_consultation(self, info):
        return self.consultation
    

#tesrresult

class TestResultOutput(graphene.ObjectType):
    id = graphene.ID()
    prescribed_test = graphene.Field('patient.schema.PrescribedTestOutput')
    laboratory = graphene.Field('patient.schema.LaboratoryOutput')
    result_file_url = graphene.String()
    notes = graphene.String()
    uploaded_at = graphene.DateTime()

    def resolve_result_file_url(self, info):
        if self.result_file:
            return info.context.build_absolute_uri(self.result_file.url)
        return None
    

#new

# output.py
import graphene
from graphene_django.types import DjangoObjectType
from .models import Doctor, LabTech, Laboratory, Symptom, Disease, Consultation, MedicalTest, PrescribedTest, TestResult

class DoctorType(DjangoObjectType):
    class Meta:
        model = Doctor

class LabTechType(DjangoObjectType):
    user = graphene.Field(lambda: CustomUserOutput)

    class Meta:
        model = LabTech

    def resolve_user(self, info):
        return self.user

class LaboratoryType(DjangoObjectType):
    class Meta:
        model = Laboratory

class SymptomType(DjangoObjectType):
    class Meta:
        model = Symptom

class DiseaseType(DjangoObjectType):
    class Meta:
        model = Disease

class ConsultationType(DjangoObjectType):
    class Meta:
        model = Consultation

class MedicalTestType(DjangoObjectType):
    class Meta:
        model = MedicalTest

class PrescribedTestType(DjangoObjectType):
    class Meta:
        model = PrescribedTest

    test = graphene.List(MedicalTestType)

    def resolve_test(self, info):
        return self.test.all()


class TestResultType(DjangoObjectType):
    class Meta:
        model = TestResult

class MedicalTestType(DjangoObjectType):
    class Meta:
        model = MedicalTest



class TestOrderType(DjangoObjectType):
    class Meta:
        model = TestOrder
        fields = "__all__"
    
    # Use your existing PatientOutput instead of PatientType
    patient = graphene.Field(PatientOutput)
    
    # Add display fields for enum choices
    priority_display = graphene.String()
    status_display = graphene.String()

    def resolve_priority_display(self, info):
        return self.get_priority_display()

    def resolve_status_display(self, info):
        return self.get_status_display()

    # Explicit patient resolver (optional)
    def resolve_patient(self, info):
        return self.patient
 
    
    # Add this if you want to resolve the patient efficiently
    def resolve_patient(self, info):
        # This will be automatically handled by DjangoObjectType,
        # but we're being explicit here for clarity
        return self.patient