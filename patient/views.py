from authApp.decorators import login_required_resolver
import graphene
from graphene import Mutation, String, Int, Float, Boolean, Date, DateTime, ID, List, Field
from graphql import GraphQLError

from .models import *
from .inputs import *
from .outputs import *

import joblib
import os
from django.conf import settings

# Load model and vectorizer once
MODEL_PATH = os.path.join(settings.BASE_DIR, 'ai', 'model', 'disease_prediction_model.pkl')
VECTORIZER_PATH = os.path.join(settings.BASE_DIR, 'ai', 'model', 'tfidf_vectorizer.pkl')

model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)
from graphene import ObjectType, Float

class DiseasePredictionType(ObjectType):
    disease = graphene.String()
    probability = graphene.Float()

class PredictDisease(graphene.Mutation):
    class Arguments:
        symptoms = graphene.String(required=True)

    # Change from single String to list of DiseasePredictionType
    predictions = graphene.List(DiseasePredictionType)

    def mutate(self, info, symptoms):
        # Transform input
        vector = vectorizer.transform([symptoms])
        
        # Get all probabilities
        probabilities = model.predict_proba(vector)[0]
        
        # Get the indices of top 3 probabilities
        top3_indices = probabilities.argsort()[-3:][::-1]
        
        # Get class names from the model
        classes = model.classes_
        
        # Prepare predictions with disease names and probabilities
        predictions = [
            {
                "disease": classes[i],
                "probability": float(probabilities[i])
            }
            for i in top3_indices
        ]
        
        return PredictDisease(predictions=predictions)

# Mutation to create/update a Patient
# views.py
from graphql_jwt.decorators import login_required

# views.py
class CreatePatient(Mutation):
    class Arguments:
        input = PatientCreateInput(required=True)

    patient = Field(PatientOutput)

    def mutate(self, info, input):
        try:
            user = User.objects.get(pk=input.user_id)
            
            patient = Patient.objects.create(
                user=user,
                date_of_birth=input.date_of_birth,
                gender=input.gender,
                medical_history=input.medical_history,
                phone_number=input.phone_number,
                address=input.address
            )
            return CreatePatient(patient=patient)
            
        except User.DoesNotExist:
            raise GraphQLError("User does not exist")

class UpdatePatient(Mutation):
    class Arguments:
        input = PatientUpdateInput(required=True)

    patient = Field(PatientOutput)

    def mutate(self, info, input):
        try:
            patient = Patient.objects.get(pk=input.id)
            
            if input.date_of_birth:
                patient.date_of_birth = input.date_of_birth
            if input.gender:
                patient.gender = input.gender
            if input.medical_history:
                patient.medical_history = input.medical_history
                
            patient.save()
            return UpdatePatient(patient=patient)
            
        except Patient.DoesNotExist:
            raise GraphQLError("Patient does not exist")



class CreateOrUpdateDoctor(Mutation):
    class Arguments:
        input = DoctorInput(required=True)

    doctor = Field(DoctorOutput)

    def mutate(self, info, input):
        user = info.context.user
        doctor, created = Doctor.objects.update_or_create(
            user=user,
            defaults={
                "specialization": input.specialization,
                "license_number": input.license_number,
                "years_of_experience": input.years_of_experience,
                "is_available": input.is_available,
                "phone_number": input.phone_number,
                "address": input.address,
            }
        )
        return CreateOrUpdateDoctor(doctor=doctor)

# Mutation to create/update a Laboratory
class CreateOrUpdateLaboratory(Mutation):
    class Arguments:
        input = LaboratoryInput(required=True)

    laboratory = Field(LaboratoryOutput)
    
    @login_required_resolver
    def mutate(self, info, input):
        user = info.context.user
        laboratory, created = Laboratory.objects.update_or_create(
            user=user,
            defaults={
                "lab_name": input.lab_name,
                "accreditation_number": input.accreditation_number,
                "location": input.location,
                "phone_number": input.phone_number,
                "address": input.address,
            }
        )
        return CreateOrUpdateLaboratory(laboratory=laboratory)

# Mutation to create/update a Symptom
class CreateOrUpdateSymptom(Mutation):
    class Arguments:
        input = SymptomInput(required=True)

    symptom = Field(SymptomOutput)

    def mutate(self, info, input):
        symptom, created = Symptom.objects.update_or_create(
            name=input.name,
            defaults={"description": input.description}
        )
        return CreateOrUpdateSymptom(symptom=symptom)

# Mutation to create/update a Disease
class CreateOrUpdateDisease(Mutation):
    class Arguments:
        input = DiseaseInput(required=True)

    disease = Field(DiseaseOutput)

    def mutate(self, info, input):
        disease, created = Disease.objects.update_or_create(
            name=input.name,
            defaults={"description": input.description}
        )
        if input.related_symptoms:
            disease.related_symptoms.set(input.related_symptoms)
        return CreateOrUpdateDisease(disease=disease)

# Mutation to create/update a Consultation
class CreateOrUpdateConsultation(Mutation):
    class Arguments:
        input = ConsultationInput(required=True)

    consultation = Field(ConsultationOutput)

    def mutate(self, info, input):
        consultation, created = Consultation.objects.update_or_create(
            id=input.id if input.id else None,
            defaults={
                "patient_id": input.patient,
                "doctor_id": input.doctor,
                "disease_id": input.disease,
                "status": input.status,
            }
        )
        if input.symptoms:
            consultation.symptoms.set(input.symptoms)
        return CreateOrUpdateConsultation(consultation=consultation)

# Mutation to create/update a MedicalTest
class CreateOrUpdateMedicalTest(Mutation):
    class Arguments:
        input = MedicalTestInput(required=True)

    medical_test = Field(MedicalTestOutput)

    def mutate(self, info, input):
        medical_test, created = MedicalTest.objects.update_or_create(
            name=input.name,
            defaults={"description": input.description}
        )
        return CreateOrUpdateMedicalTest(medical_test=medical_test)

# Mutation to prescribe a MedicalTest
class PrescribeTest(Mutation):
    class Arguments:
        input = PrescribedTestInput(required=True)

    prescribed_test = Field(PrescribedTestOutput)

    def mutate(self, info, input):
        prescribed_test = PrescribedTest.objects.create(
            consultation_id=input.consultation,
            test_id=input.test,
            notes=input.notes
        )
        return PrescribeTest(prescribed_test=prescribed_test)

# Mutation to upload Test Results
class UploadTestResult(Mutation):
    class Arguments:
        input = TestResultInput(required=True)

    test_result = Field(TestResultOutput)

    def mutate(self, info, input):
        test_result = TestResult.objects.create(
            prescribed_test_id=input.prescribed_test,
            laboratory_id=input.laboratory,
            result_file=input.result_file,
            notes=input.notes
        )
        return UploadTestResult(test_result=test_result)

# Mutation to create/update a Prescription
class CreateOrUpdatePrescription(Mutation):
    class Arguments:
        input = PrescriptionInput(required=True)

    prescription = Field(PrescriptionOutput)

    def mutate(self, info, input):
        prescription, created = Prescription.objects.update_or_create(
            consultation_id=input.consultation,
            defaults={
                "medication": input.medication,
                "dosage": input.dosage,
                "instructions": input.instructions,
            }
        )
        return CreateOrUpdatePrescription(prescription=prescription)





import base64
import datetime
from django.core.files.base import ContentFile

class CreateTestResult(Mutation):
    class Arguments:
        input = TestResultInput(required=True)

    test_result = Field(TestResultOutput)

    @classmethod
    def mutate(cls, root, info, input):
        try:
            # Validate inputs
            prescribed_test = PrescribedTest.objects.get(pk=input.prescribed_test_id)
            laboratory = Laboratory.objects.get(pk=input.laboratory_id)

            # Decode base64 file
            file_data = base64.b64decode(input.result_file)
            file_content = ContentFile(file_data, name=input.file_name)

            # Create test result
            test_result = TestResult.objects.create(
                prescribed_test=prescribed_test,
                laboratory=laboratory,
                result_file=file_content,
                notes=input.notes
            )

            return CreateTestResult(test_result=test_result)

        except PrescribedTest.DoesNotExist:
            raise Exception("Prescribed test not found")
        except Laboratory.DoesNotExist:
            raise Exception("Laboratory not found")
        except Exception as e:
            raise Exception(f"Failed to create test result: {str(e)}")















#new

import graphene
from graphene_file_upload.scalars import Upload
from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from .models import *
from .inputs import *
from .schema import *

# Create Mutations (previous ones remain...)
class CreateDoctor(graphene.Mutation):
    class Arguments:
        input = DoctorInput(required=True)

    doctor = graphene.Field(DoctorType)
    
    @staticmethod
    def mutate(root, info, input):
        doctor = Doctor(
            user_id=input.user_id,
            specialization=input.specialization,
            license_number=input.license_number,
            years_of_experience=input.years_of_experience,
            is_available=input.is_available
        )
        doctor.save()
        return CreateDoctor(doctor=doctor)

class CreateLabTech(graphene.Mutation):
    class Arguments:
        input = LabTechInput(required=True)

    lab_tech = graphene.Field(LabTechType)

    @staticmethod
    def mutate(root, info, input):
        try:
            user = get_user_model().objects.get(pk=input.user_id)
        except get_user_model().DoesNotExist:
            raise GraphQLError("User not found")

        lab_tech = LabTech.objects.create(
            user=user,
            specialization=input.specialization,
            license_number=input.license_number,
            years_of_experience=input.years_of_experience,
            is_available=input.is_available if input.is_available is not None else True,
            phone_number=input.phone_number,
            address=input.address
        )

        return CreateLabTech(lab_tech=lab_tech)

 
class CreateLaboratory(graphene.Mutation):
    class Arguments:
        input = LaboratoryInput(required=True)

    laboratory = graphene.Field(LaboratoryType)
    
    @staticmethod
    def mutate(root, info, input):
        try:
            user = get_user_model().objects.get(pk=input.user_id)
        except get_user_model().DoesNotExist:
            raise GraphQLError("User with provided ID does not exist.")

        laboratory = Laboratory.objects.create(
            user=user,
            lab_tech_id=input.lab_tech_id if input.lab_tech_id else None,
            lab_name=input.lab_name,
            accreditation_number=input.accreditation_number,
            location=input.location
        )
        return CreateLaboratory(laboratory=laboratory)

class CreateSymptom(graphene.Mutation):
    class Arguments:
        input = SymptomInput(required=True)

    symptom = graphene.Field(SymptomType)
    
    @staticmethod
    def mutate(root, info, input):
        symptom = Symptom(
            name=input.name,
            description=input.description,
            swahili_name=input.swahili_name
        )
        symptom.save()
        return CreateSymptom(symptom=symptom)

class CreateDisease(graphene.Mutation):
    class Arguments:
        input = DiseaseInput(required=True)

    disease = graphene.Field(DiseaseType)
    
    @staticmethod
    def mutate(root, info, input):
        disease = Disease(
            name=input.name,
            description=input.description
        )
        disease.save()
        
        # Handle many-to-many relationships
        if input.related_symptoms:
            disease.related_symptoms.set(input.related_symptoms)
        if input.doctors:
            disease.doctors.set(input.doctors)
            
        return CreateDisease(disease=disease)

class CreateConsultation(graphene.Mutation):
    class Arguments:
        input = ConsultationInput(required=True)

    consultation = graphene.Field(ConsultationType)
    
    @staticmethod
    def mutate(root, info, input):
        consultation = Consultation(
            patient_id=input.patient_id,
            doctor_id=input.doctor_id if input.doctor_id else None,
            disease_id=input.disease_id if input.disease_id else None,
            status=input.status if input.status else 'Pending'
        )
        consultation.save()
        
        if input.symptoms:
            consultation.symptoms.set(input.symptoms)
            
        return CreateConsultation(consultation=consultation)

class CreateMedicalTest(graphene.Mutation):
    class Arguments:
        input = MedicalTestInput(required=True)

    medical_test = graphene.Field(MedicalTestType)

    def mutate(self, info, input):
        medical_test = MedicalTest.objects.create(
            name=input.name,
            description=input.description
        )
        return CreateMedicalTest(medical_test=medical_test)


class UpdateMedicalTest(graphene.Mutation):
    class Arguments:
        input = MedicalTestInput(required=True)

    medical_test = graphene.Field(MedicalTestType)

    def mutate(self, info, input):
        try:
            medical_test = MedicalTest.objects.get(pk=input.id)
        except MedicalTest.DoesNotExist:
            raise GraphQLError("MedicalTest not found.")

        medical_test.name = input.name
        medical_test.description = input.description
        medical_test.save()
        return UpdateMedicalTest(medical_test=medical_test)


class DeleteMedicalTest(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
        try:
            medical_test = MedicalTest.objects.get(pk=id)
            medical_test.delete()
            return DeleteMedicalTest(success=True)
        except MedicalTest.DoesNotExist:
            raise GraphQLError("MedicalTest not found.")

class CreatePrescribedTest(graphene.Mutation):
    class Arguments:
        input = PrescribedTestInput(required=True)

    prescribed_test = graphene.Field(PrescribedTestType)
    
    @staticmethod
    def mutate(root, info, input):
        prescribed_test = PrescribedTest(
            consultation_id=input.consultation_id,
            notes=input.notes
        )
        prescribed_test.save()
        
        if input.test_ids:
            prescribed_test.test.set(input.test_ids)
            
        return CreatePrescribedTest(prescribed_test=prescribed_test)

class CreateTestResult(graphene.Mutation):
    class Arguments:
        input = TestResultInput(required=True)
        result_file = Upload()

    test_result = graphene.Field(TestResultType)
    
    @staticmethod
    def mutate(root, info, input, result_file=None):
        test_result = TestResult(
            prescribed_test_id=input.prescribed_test_id,
            laboratory_id=input.laboratory_id,
            notes=input.notes,
            result_file=result_file
        )
        test_result.save()
        return CreateTestResult(test_result=test_result)

class CreatePrescription(graphene.Mutation):
    class Arguments:
        input = PrescriptionInput(required=True)

    prescription = graphene.Field(PrescriptionOutput)
    
    @staticmethod
    def mutate(root, info, input):
        prescription = Prescription(
            consultation_id=input.consultation_id,
            medication=input.medication,
            dosage=input.dosage,
            instructions=input.instructions
        )
        prescription.save()
        return CreatePrescription(prescription=prescription)

# Update Mutations
class UpdateDoctor(graphene.Mutation):
    class Arguments:
        input = DoctorInput(required=True)

    doctor = graphene.Field(DoctorType)
    
    @staticmethod
    def mutate(root, info, input):
        try:
            doctor = Doctor.objects.get(pk=input.id)
            if input.specialization:
                doctor.specialization = input.specialization
            if input.license_number:
                doctor.license_number = input.license_number
            if input.years_of_experience is not None:
                doctor.years_of_experience = input.years_of_experience
            if input.is_available is not None:
                doctor.is_available = input.is_available
            doctor.save()
            return UpdateDoctor(doctor=doctor)
        except ObjectDoesNotExist:
            raise GraphQLError(f"Doctor with id {input.id} does not exist")

class UpdateLabTech(graphene.Mutation):
    class Arguments:
        input = LabTechInput(required=True)

    lab_tech = graphene.Field(LabTechType)
    
    @staticmethod
    def mutate(root, info, input):
        try:
            lab_tech = LabTech.objects.get(pk=input.id)
            if input.specialization:
                lab_tech.specialization = input.specialization
            if input.license_number:
                lab_tech.license_number = input.license_number
            if input.years_of_experience is not None:
                lab_tech.years_of_experience = input.years_of_experience
            if input.is_available is not None:
                lab_tech.is_available = input.is_available
            lab_tech.save()
            return UpdateLabTech(lab_tech=lab_tech)
        except ObjectDoesNotExist:
            raise GraphQLError(f"LabTech with id {input.id} does not exist")

class UpdateDisease(graphene.Mutation):
    class Arguments:
        input = DiseaseInput(required=True)

    disease = graphene.Field(DiseaseType)
    
    @staticmethod
    def mutate(root, info, input):
        try:
            disease = Disease.objects.get(pk=input.id)
            if input.name:
                disease.name = input.name
            if input.description:
                disease.description = input.description
            
            if input.related_symptoms is not None:
                disease.related_symptoms.set(input.related_symptoms)
            if input.doctors is not None:
                disease.doctors.set(input.doctors)
            
            disease.save()
            return UpdateDisease(disease=disease)
        except ObjectDoesNotExist:
            raise GraphQLError(f"Disease with id {input.id} does not exist")

class UpdateConsultation(graphene.Mutation):
    class Arguments:
        input = ConsultationInput(required=True)

    consultation = graphene.Field(ConsultationType)
    
    @staticmethod
    def mutate(root, info, input):
        try:
            consultation = Consultation.objects.get(pk=input.id)
            if input.doctor_id:
                consultation.doctor_id = input.doctor_id
            if input.disease_id:
                consultation.disease_id = input.disease_id
            if input.status:
                consultation.status = input.status
            
            if input.symptoms is not None:
                consultation.symptoms.set(input.symptoms)
            
            consultation.save()
            return UpdateConsultation(consultation=consultation)
        except ObjectDoesNotExist:
            raise GraphQLError(f"Consultation with id {input.id} does not exist")

class UpdatePrescribedTest(graphene.Mutation):
    class Arguments:
        input = PrescribedTestInput(required=True)

    prescribed_test = graphene.Field(PrescribedTestType)
    
    @staticmethod
    def mutate(root, info, input):
        try:
            prescribed_test = PrescribedTest.objects.get(pk=input.id)
            if input.notes:
                prescribed_test.notes = input.notes
            
            if input.test_ids is not None:
                prescribed_test.test.set(input.test_ids)
            
            prescribed_test.save()
            return UpdatePrescribedTest(prescribed_test=prescribed_test)
        except ObjectDoesNotExist:
            raise GraphQLError(f"PrescribedTest with id {input.id} does not exist")

# Delete Mutations
class DeleteDoctor(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    
    @staticmethod
    def mutate(root, info, id):
        try:
            doctor = Doctor.objects.get(pk=id)
            doctor.delete()
            return DeleteDoctor(success=True)
        except ObjectDoesNotExist:
            raise GraphQLError(f"Doctor with id {id} does not exist")

class DeleteDisease(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    
    @staticmethod
    def mutate(root, info, id):
        try:
            disease = Disease.objects.get(pk=id)
            disease.delete()
            return DeleteDisease(success=True)
        except ObjectDoesNotExist:
            raise GraphQLError(f"Disease with id {id} does not exist")

class DeleteConsultation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    
    @staticmethod
    def mutate(root, info, id):
        try:
            consultation = Consultation.objects.get(pk=id)
            consultation.delete()
            return DeleteConsultation(success=True)
        except ObjectDoesNotExist:
            raise GraphQLError(f"Consultation with id {id} does not exist")

# Add similar delete mutations for other models...

class PatientMutation(graphene.ObjectType):

    #new
    
    create_doctor = CreateDoctor.Field()
    update_doctor = UpdateDoctor.Field()
    delete_doctor = DeleteDoctor.Field()
    create_labtech = CreateLabTech.Field()
    update_labtech = UpdateLabTech.Field()
    create_laboratory = CreateLaboratory.Field()



    # Create
    create_doctor = CreateDoctor.Field()
    create_lab_tech = CreateLabTech.Field()
    create_laboratory = CreateLaboratory.Field()
    create_symptom = CreateSymptom.Field()
    create_disease = CreateDisease.Field()
    create_consultation = CreateConsultation.Field()
    create_prescribed_test = CreatePrescribedTest.Field()
    create_test_result = CreateTestResult.Field()
    create_prescription = CreatePrescription.Field()
    
    # Update
    update_doctor = UpdateDoctor.Field()
    update_lab_tech = UpdateLabTech.Field()
    update_disease = UpdateDisease.Field()
    update_consultation = UpdateConsultation.Field()
    update_prescribed_test = UpdatePrescribedTest.Field()
    
    # Delete
    delete_doctor = DeleteDoctor.Field()
    delete_disease = DeleteDisease.Field()
    delete_consultation = DeleteConsultation.Field()
    # Add other delete mutations...
# Root Mutation
    create_patient = CreatePatient.Field()
    update_patient = UpdatePatient.Field()
    create_or_update_doctor = CreateOrUpdateDoctor.Field()
    create_or_update_laboratory = CreateOrUpdateLaboratory.Field()
    create_or_update_symptom = CreateOrUpdateSymptom.Field()
    create_or_update_disease = CreateOrUpdateDisease.Field()
    create_or_update_consultation = CreateOrUpdateConsultation.Field()
    create_or_update_medical_test = CreateOrUpdateMedicalTest.Field()
    prescribe_test = PrescribeTest.Field()
    upload_test_result = UploadTestResult.Field()
    create_or_update_prescription = CreateOrUpdatePrescription.Field()
    predict_disease = PredictDisease.Field()
    create_test_result = CreateTestResult.Field()

    create_medical_test = CreateMedicalTest.Field()
    update_medical_test = UpdateMedicalTest.Field()
    delete_medical_test = DeleteMedicalTest.Field()



# api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model

User = get_user_model()

class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = User.objects.exclude(id=request.user.id)
        data = [{'id': user.id, 'username': user.username} for user in users]
        return Response(data)
