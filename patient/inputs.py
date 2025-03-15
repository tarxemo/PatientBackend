import graphene
from graphene import InputObjectType, String, Int, Float, Boolean, Date, DateTime, ID
from graphene_django.types import DjangoObjectType
from .models import (
    Patient, Doctor, Laboratory, Symptom, Disease, Consultation,
    MedicalTest, PrescribedTest, TestResult, Prescription
)

# Input for BaseProfile (abstract model)
class BaseProfileInput(InputObjectType):
    phone_number = String()
    address = String()

# Input for Patient
class PatientInput(BaseProfileInput):
    date_of_birth = Date(required=True)
    gender = String(required=True)
    medical_history = String()

# Input for Doctor
class DoctorInput(BaseProfileInput):
    specialization = String(required=True)
    license_number = String(required=True)
    years_of_experience = Int(required=True)
    is_available = Boolean()

# Input for Laboratory
class LaboratoryInput(BaseProfileInput):
    lab_name = String(required=True)
    accreditation_number = String(required=True)
    location = String(required=True)

# Input for Symptom
class SymptomInput(InputObjectType):
    name = String(required=True)
    description = String()

# Input for Disease
class DiseaseInput(InputObjectType):
    name = String(required=True)
    description = String()
    related_symptoms = graphene.List(ID)  # List of Symptom IDs

# Input for Consultation
class ConsultationInput(InputObjectType):
    patient = ID(required=True)  # Patient ID
    doctor = ID()  # Doctor ID (optional)
    symptoms = graphene.List(ID)  # List of Symptom IDs
    disease = ID()  # Disease ID (optional)
    status = String()

# Input for MedicalTest
class MedicalTestInput(InputObjectType):
    name = String(required=True)
    description = String()

# Input for PrescribedTest
class PrescribedTestInput(InputObjectType):
    consultation = ID(required=True)  # Consultation ID
    test = ID(required=True)  # MedicalTest ID
    notes = String()

# Input for TestResult
class TestResultInput(InputObjectType):
    prescribed_test = ID(required=True)  # PrescribedTest ID
    laboratory = ID(required=True)  # Laboratory ID
    result_file = String(required=True)  # File path or URL
    notes = String()

# Input for Prescription
class PrescriptionInput(InputObjectType):
    consultation = ID(required=True)  # Consultation ID
    medication = String(required=True)
    dosage = String(required=True)
    instructions = String()