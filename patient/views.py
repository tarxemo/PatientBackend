from authApp.decorators import login_required_resolver
import graphene
from graphene import Mutation, String, Int, Float, Boolean, Date, DateTime, ID, List, Field
from .models import (
    Patient, Doctor, Laboratory, Symptom, Disease, Consultation,
    MedicalTest, PrescribedTest, TestResult, Prescription
)
from .inputs import (
    PatientInput, DoctorInput, LaboratoryInput, SymptomInput, DiseaseInput,
    ConsultationInput, MedicalTestInput, PrescribedTestInput, TestResultInput, PrescriptionInput
)
from .outputs import (
    PatientOutput, DoctorOutput, LaboratoryOutput, SymptomOutput, DiseaseOutput,
    ConsultationOutput, MedicalTestOutput, PrescribedTestOutput, TestResultOutput, PrescriptionOutput
)

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
class CreateOrUpdatePatient(Mutation):
    class Arguments:
        input = PatientInput(required=True)

    patient = Field(PatientOutput)

    def mutate(self, info, input):
        user = info.context.user
        patient, created = Patient.objects.update_or_create(
            user=user,
            defaults={
                "date_of_birth": input.date_of_birth,
                "gender": input.gender,
                "medical_history": input.medical_history,
                "phone_number": input.phone_number,
                "address": input.address,
            }
        )
        return CreateOrUpdatePatient(patient=patient)

# Mutation to create/update a Doctor
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

# Root Mutation
class PatientMutation(graphene.ObjectType):
    create_or_update_patient = CreateOrUpdatePatient.Field()
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
