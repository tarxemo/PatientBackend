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
# inputs.py
class PatientCreateInput(BaseProfileInput):
    date_of_birth = Date(required=True)
    gender = String(required=True)
    medical_history = String()
    user_id = ID(required=True)  # For linking to existing user

class PatientUpdateInput(BaseProfileInput):
    id = ID(required=True)  # Required for updates
    date_of_birth = Date()
    gender = String()
    medical_history = String()
# Input for Doctor
class DoctorInput(BaseProfileInput):
    specialization = String(required=True)
    license_number = String(required=True)
    years_of_experience = Int(required=True)
    is_available = Boolean()

# Input for Laboratory
class LaboratoryInput(BaseProfileInput):
    lab_technitian_id = graphene.ID()
    lab_name = String(required=True)
    accreditation_number = String(required=True)
    location = String(required=True)
    email=String(required=True)
    description=String()
    address=String()
    

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
    medical_test = ID(required=True)  # MedicalTest ID
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
    # medication = String(required=True)
    dosage = String(required=True)
    instructions = String()


class TestResultInput(graphene.InputObjectType):
    prescribed_test_id = graphene.ID(required=True, description="ID of the prescribed test")
    laboratory_id = graphene.ID(required=True, description="ID of the laboratory")
    result_file = graphene.String(required=True, description="Base64 encoded file content")
    file_name = graphene.String(required=True, description="Name of the file with extension")
    notes = graphene.String(description="Additional notes about the test result")

class MedicalTestInput(graphene.InputObjectType):
    id = graphene.ID()
    name = graphene.String(required=True)
    description = graphene.String()

from graphene import InputObjectType, ID, DateTime, String, Boolean

class AppointmentInput(InputObjectType):
    doctor = ID(required=True)  
    date_time = DateTime(required=True)  
    location = String(required=True) 
    status = String(default_value="scheduled")  
    notes = String()  




#new

# inputs.py
import graphene
from graphene_django.forms.mutation import DjangoModelFormMutation
from graphql import GraphQLError
from .models import Doctor, LabTech, Laboratory, Symptom, Disease, Consultation, MedicalTest, PrescribedTest, TestResult
from django.contrib.auth import get_user_model

class DoctorInput(graphene.InputObjectType):
    id = graphene.ID()
    user_id = graphene.ID(required=True)
    specialization = graphene.String(required=True)
    license_number = graphene.String(required=True)
    years_of_experience = graphene.Int(required=True)
    is_available = graphene.Boolean()

class LabTechInput(graphene.InputObjectType):
    id = graphene.ID()
    user_id = graphene.ID(required=True)
    specialization = graphene.String(required=True)
    license_number = graphene.String(required=True)
    years_of_experience = graphene.Int(required=True)
    is_available = graphene.Boolean()
    phone_number = graphene.String()
    address = graphene.String()

# class LaboratoryInput(graphene.InputObjectType):
#     id = graphene.ID()
#     lab_tech_id = graphene.ID()
#     lab_name = graphene.String(required=True)
#     accreditation_number = graphene.String(required=True)
#     location = graphene.String(required=True)

class SymptomInput(graphene.InputObjectType):
    id = graphene.ID()
    name = graphene.String(required=True)
    description = graphene.String()
    swahili_name = graphene.String()

class DiseaseInput(graphene.InputObjectType):
    id = graphene.ID()
    name = graphene.String(required=True)
    description = graphene.String()
    related_symptoms = graphene.List(graphene.ID)
    doctors = graphene.List(graphene.ID)

class ConsultationInput(graphene.InputObjectType):
    id = graphene.ID()
    patient_id = graphene.ID(required=True)
    doctor_id = graphene.ID()
    symptoms = graphene.List(graphene.ID)
    disease_id = graphene.ID()
    status = graphene.String()

class MedicalTestInput(graphene.InputObjectType):
    id = graphene.ID()
    name = graphene.String(required=True)
    description = graphene.String()

class PrescribedTestInput(graphene.InputObjectType):
    id = graphene.ID()
    consultation_id = graphene.ID(required=True)
    test_ids = graphene.List(graphene.ID, required=True)
    notes = graphene.String()

class TestResultInput(graphene.InputObjectType):
    id = graphene.ID()
    prescribed_test_id = graphene.ID(required=True)
    laboratory_id = graphene.ID(required=True)
    result_file = graphene.String()  # path or base64 string depending on setup
    notes = graphene.String()


# schema/inputs.py
import graphene
from graphene_django.types import DjangoObjectType
from .models import TestOrder

class TestOrderInput(graphene.InputObjectType):
    test_type_id = graphene.ID(required=True)
    patient_id = graphene.ID(required=True)
    priority = graphene.String()
    status = graphene.String()

class TestOrderUpdateInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    priority = graphene.String()
    status = graphene.String()
