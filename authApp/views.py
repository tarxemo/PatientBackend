from contextvars import Token
import uuid
from authApp.decorators import login_required_resolver
import graphene
from graphene import Mutation
from .models import *
from .inputs import *
from .outputs import *
from django.contrib.auth import authenticate
from graphql import GraphQLError
from rest_framework_simplejwt.tokens import RefreshToken
from graphql import GraphQLError
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.core.cache import cache


import os
import shutil
import subprocess
import json
import joblib
import whisper
import numpy as np
import pandas as pd
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from patient.models import Disease  # Assuming Disease model exists


class LoginMutation(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    access_token = graphene.String()
    refresh_token = graphene.String()
    user = graphene.Field(CustomUserOutput)

    def mutate(self, info, username, password):
        user = authenticate(username=username, password=password)
        if not user:
            raise GraphQLError("Invalid credentials")

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        return LoginMutation(
            access_token=str(refresh.access_token),
            refresh_token=str(refresh),
            user=user,
        )


class RefreshTokenMutation(graphene.Mutation):
    class Arguments:
        refresh_token = graphene.String(required=True)

    access_token = graphene.String()

    def mutate(self, info, refresh_token):
        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            return RefreshTokenMutation(access_token=access_token)
        except Exception as e:
            raise GraphQLError("Invalid refresh token")


class LogoutMutation(graphene.Mutation):
    success = graphene.Boolean()

    @login_required_resolver
    def mutate(self, info):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("Not authenticated")

        # Blacklist the refresh token (if using Django SimpleJWT's token blacklist feature)
        return LogoutMutation(success=True)


# Mutation to create a new user
class CreateUser(Mutation):
    class Arguments:
        user_data = UserInput(required=True)  # Changed to required=True

    user = graphene.Field(CustomUserOutput)

    def mutate(self, info, user_data):
        try:
            # Create user with all fields
            user = CustomUser(
                username=user_data.username,
                email=user_data.email,
                user_type=user_data.user_type if hasattr(user_data, 'user_type') else 'PATIENT',
                phone_number=user_data.phone_number if hasattr(user_data, 'phone_number') else None,
                address=user_data.address if hasattr(user_data, 'address') else None,
                profile_picture=user_data.profile_picture if hasattr(user_data, 'profile_picture') else None,
                date_of_birth=user_data.date_of_birth if hasattr(user_data, 'date_of_birth') else None,
                is_verified=user_data.is_verified if hasattr(user_data, 'is_verified') else False,
                first_name=user_data.first_name if hasattr(user_data, 'first_name') else '',
                last_name=user_data.last_name if hasattr(user_data, 'last_name') else ''
            )
            
            user.set_password(user_data.password)
            user.save()
            
            return CreateUser(user=user)
            
        except Exception as e:
            raise GraphQLError(f"User creation failed: {str(e)}")
        

# Define Mutation
class UpdateCustomUser(Mutation):
    class Arguments:
        user_data = UserUpdateInput(required=True)
        user_id = graphene.ID(required=True)  # Now required since we're not using context user

    user = graphene.Field(CustomUserOutput)

    def mutate(self, info, user_data, user_id):
        try:
            # Get user by provided ID (no auth check)
            user = CustomUser.objects.get(id=user_id)

            # Handle password update if provided
            if hasattr(user_data, 'old_password') and hasattr(user_data, 'new_password'):
                if not check_password(user_data.old_password, user.password):
                    raise GraphQLError("Old password is incorrect")
                
                if user_data.new_password != getattr(user_data, 'confirm_password', None):
                    raise GraphQLError("New passwords don't match")
                
                if check_password(user_data.new_password, user.password):
                    raise GraphQLError("New password cannot be the same as old password")
                
                user.set_password(user_data.new_password)

            # Update regular fields
            update_fields = []
            for field in [
                'username', 'first_name', 'last_name', 'email',
                'user_type', 'phone_number', 'address',
                'profile_picture', 'date_of_birth', 'is_verified'
            ]:
                if hasattr(user_data, field):
                    new_value = getattr(user_data, field)
                    if new_value is not None:
                        setattr(user, field, new_value)
                        update_fields.append(field)

            user.save(update_fields=update_fields)
            return UpdateCustomUser(user=user)

        except CustomUser.DoesNotExist:
            raise GraphQLError("User not found")
        except Exception as e:
            raise GraphQLError(f"Update failed: {str(e)}")
# Mutation to delete a user
class DeleteCustomUser(Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
        user = CustomUser.objects.get(id=id)
        user.delete()
        return DeleteCustomUser(success=True)


class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    update_user = UpdateCustomUser.Field()
    delete_user = DeleteCustomUser.Field()
    login = LoginMutation.Field()
    refresh_token = RefreshTokenMutation.Field()
    logout = LogoutMutation.Field()
    
    

import os
import shutil
import subprocess
import json
import joblib
# import whisper
import numpy as np
import pandas as pd
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.views import APIView
from patient.models import Disease, Symptom  # Assuming Disease model exists

# Load Whisper speech-to-text model
# whisper_model = whisper.load_model("large")

# Load disease prediction model and necessary files
disease_model = joblib.load('disease_prediction_model.pkl')
label_encoder = joblib.load('label_encoder.pkl')
expected_columns = joblib.load('feature_names.pkl')

# Load symptom translations
with open('symptom_translation.json', 'r', encoding='utf-8') as f:
    symptom_translation = json.load(f)

class TranscribeAndPredictDiseaseView(APIView):
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def convert_audio_to_16khz(self, audio_path):
        """
        Convert audio to 16-bit PCM mono, 16kHz using ffmpeg.
        Removes silence and normalizes volume to improve STT performance.
        """
        base, ext = os.path.splitext(audio_path)
        output_path = base + "_processed.wav"

        if not shutil.which("ffmpeg"):
            raise FileNotFoundError("FFmpeg is not installed. Please install it and try again.")

        if not os.path.exists(output_path):
            # Build FFmpeg command
            command = [
                "ffmpeg",
                "-i", audio_path,
                "-ac", "1",             # Mono channel
                "-ar", "16000",         # 16kHz sample rate
                "-af", "volume=1.5, dynaudnorm",  # Normalize volume
                "-c:a", "pcm_s16le",    # 16-bit PCM
                "-y",                   # Overwrite output
                output_path
            ]

            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return output_path


    def match_symptoms(self, text):
        """Convert user text into symptom feature vector for model."""
        result = {}
        for key, value in symptom_translation.items():
            modified_key = key.replace(" ", "_")  # Ensure consistency with feature names
            key_words = key.split()
            key_match = sum(1 for word in key_words if word.lower() in text.lower()) / len(key_words)
            value_words = value.split()
            value_match = sum(1 for word in value_words if word.lower() in text.lower()) / len(value_words)
            overall_match = (key_match + value_match) / 2
            result[modified_key] = 1 if overall_match > 0.2 else 0
        return result

    def post(self, request, *args, **kwargs):
        """Handle both initial submission and follow-up questions"""
        # Check if this is a follow-up request
        if 'question_id' in request.data:
            return self.follow_up(request, *args, **kwargs)
        else:
            return self.initial_analysis(request, *args, **kwargs)
        
    def initial_analysis(self, request, *args, **kwargs):
        """Handle file upload, transcription, and disease prediction."""
        if "audio_file" not in request.FILES:
            symptoms_text = request.POST.get("symptoms_text")
            print(symptoms_text)
            if symptoms_text:
                pass
            else:
                return Response({"error": "No audio file  provided"}, status=status.HTTP_400_BAD_REQUEST)

        if "audio_file" in request.FILES:
            # Define the upload directory
            upload_dir = os.path.join(settings.MEDIA_ROOT, "uploads")
            os.makedirs(upload_dir, exist_ok=True)

            # Save uploaded file
            audio_file = request.FILES["audio_file"]
            file_path = os.path.join(upload_dir, f"{uuid.uuid4().hex}_{audio_file.name}")
            with open(file_path, "wb+") as destination:
                for chunk in audio_file.chunks():
                    destination.write(chunk)

            # Convert and transcribe the audio
            converted_audio = self.convert_audio_to_16khz(file_path)
            transcription_result = whisper_model.transcribe(converted_audio, language="english")
            transcribed_text = transcription_result["text"]
        else:
            transcribed_text=symptoms_text
        # Convert transcribed text into a feature vector
        matched_symptoms = self.match_symptoms(transcribed_text)
        print(transcribed_text)
        # Convert to DataFrame and ensure it matches model input format
        df_test = pd.DataFrame([matched_symptoms])
        df_test = df_test.reindex(columns=expected_columns, fill_value=0)

        # Make predictions
        y_prob_test = disease_model.predict_proba(df_test)

        # Get top 5 predicted diseases
        top_5_indices = np.argsort(y_prob_test[0])[::-1][:5]
        top_5_predictions = label_encoder.classes_[top_5_indices]
        top_5_probabilities = y_prob_test[0][top_5_indices] * 100

        symptom_questions = self.generate_symptom_questions(top_5_predictions)
        
        session_id = str(uuid.uuid4())
        
        # Store diagnosis state in cache (or database)
        diagnosis_state = {
            'current_predictions': top_5_predictions.tolist(),
            'current_probabilities': top_5_probabilities.tolist(),
            'asked_questions': [],
            'user_responses': {},
            'transcribed_text': transcribed_text
        }
        cache.set(f'diagnosis_{session_id}', diagnosis_state, timeout=3600)
        
        # Retrieve disease details from the database
        diseases_data = []
        for i in range(5):
            disease_name = top_5_predictions[i]
            disease_instance = Disease.objects.filter(name=disease_name).first()
            if disease_instance:
                diseases_data.append({
                    "name": disease_instance.name,
                    "description": disease_instance.description,
                    "common_symptoms": list(disease_instance.related_symptoms.values_list('name', flat=True)),  # Convert to list
                    "probability": round(top_5_probabilities[i], 2)
                })


        # Prepare the response
        response_data = {
            "transcript": transcribed_text,
            "predicted_diseases": diseases_data,
            "questions": symptom_questions,
            "diagnosis_session": session_id,
            "stage": "followup"
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def generate_symptom_questions(self, diseases, asked_questions = ""):
        """Generate questions based on most differentiating symptoms"""
        diseases_qs = Disease.objects.filter(name__in=diseases)
        
        # Get all symptoms for these diseases that haven't been asked yet
        if asked_questions == "":
            all_symptoms = (Symptom.objects
                    .filter(related_diseases__in=diseases_qs)
                    .distinct())
        else:
            all_symptoms = (Symptom.objects
                    .filter(related_diseases__in=diseases_qs)
                    .exclude(id__in=asked_questions)
                    .distinct())
        
        # Calculate symptom importance scores
        symptom_scores = []
        for symptom in all_symptoms:
            # Diseases that have this symptom
            positive_diseases = diseases_qs.filter(related_symptoms=symptom)
            positive_count = positive_diseases.count()
            negative_count = len(diseases) - positive_count
            
            # Calculate information gain (how well it splits the diseases)
            if positive_count == 0 or negative_count == 0:
                continue  # Skip symptoms that don't differentiate
                
            # Score based on how balanced the split is and symptom frequency
            score = (min(positive_count, negative_count) / len(diseases)) * (1 / (positive_count + 1))
            symptom_scores.append((symptom, score))
        
        # Sort by most differentiating symptoms
        symptom_scores.sort(key=lambda x: -x[1])
        
        # Return top 3 most differentiating questions
        questions = [{
            'id': s.id,
            'text': f"Do you have {s.name.lower()}?",
            'type': 'boolean'
        } for s, _ in symptom_scores[:3]]
        
        return questions

    def calculate_probabilities(self, diseases, user_responses):
        """Calculate updated probabilities based on user responses"""
        diseases_qs = Disease.objects.filter(name__in=diseases)
        disease_list = list(diseases_qs)
        
        # Initialize base probabilities (equal for all diseases)
        probabilities = {d.name: 1.0 for d in disease_list}
        total = len(disease_list)
        
        # Adjust probabilities based on responses
        for symptom_id, response in user_responses.items():
            symptom = Symptom.objects.get(id=symptom_id)
            
            for disease in disease_list:
                has_symptom = disease.related_symptoms.filter(id=symptom.id).exists()
                
                # If user said yes and disease has symptom, increase probability
                if response and has_symptom:
                    probabilities[disease.name] *= 2.0  # Double the weight
                # If user said no and disease doesn't have symptom, increase probability
                elif not response and not has_symptom:
                    probabilities[disease.name] *= 1.5
                # If mismatch (user has symptom disease doesn't, or vice versa), decrease
                else:
                    probabilities[disease.name] *= 0.6
        
        # Normalize probabilities to sum to 100%
        total_prob = sum(probabilities.values())
        normalized_probs = {
            name: (prob / total_prob) * 100 
            for name, prob in probabilities.items()
        }
        
        return normalized_probs

    def follow_up(self, request, *args, **kwargs):
        # Get session ID from request
        session_id = request.data.get('diagnosis_session')
        if not session_id:
            return Response({"error": "Missing diagnosis session"}, status=400)
        
        # Retrieve state from cache
        diagnosis_state = cache.get(f'diagnosis_{session_id}')
        if not diagnosis_state:
            return Response({"error": "Session expired or invalid"}, status=400)
        
        # Get user response
        question_id = request.data.get('question_id')
        response = request.data.get('response')
        
        # Store the response
        diagnosis_state['user_responses'][str(question_id)] = response
        diagnosis_state['asked_questions'].append(question_id)
        
        # Update probabilities based on all responses
        updated_probs = self.calculate_probabilities(
            diagnosis_state['current_predictions'],
            diagnosis_state['user_responses']
        )
        
        # Sort diseases by probability
        sorted_diseases = sorted(
            updated_probs.items(),
            key=lambda x: -x[1]
        )
        
        # Get top diseases (minimum 20% probability to keep)
        top_diseases = [
            name for name, prob in sorted_diseases 
            if prob >= 20.0 or prob == sorted_diseases[0][1]
        ]
        
        # Update state
        diagnosis_state['current_predictions'] = top_diseases
        diagnosis_state['current_probabilities'] = {
            name: updated_probs[name] 
            for name in top_diseases
        }
        
        # Get disease details
        diseases_data = []
        for disease_name in top_diseases:
            disease_instance = Disease.objects.filter(name=disease_name).first()
            if disease_instance:
                diseases_data.append({
                    "name": disease_instance.name,
                    "probability": round(updated_probs[disease_name], 2),
                    "common_symptoms": list(disease_instance.related_symptoms.values_list('name', flat=True))
                })
        
        # Determine if we should conclude
        if len(top_diseases) == 1 or sorted_diseases[0][1] > 80.0:
            stage = "conclusion"
            new_questions = []
        else:
            stage = "followup"
            new_questions = self.generate_symptom_questions(
                top_diseases,
                diagnosis_state['asked_questions']
            )
        
        # Save updated state
        cache.set(f'diagnosis_{session_id}', diagnosis_state, timeout=3600)
        
        return Response({
            "predicted_diseases": diseases_data,
            "questions": new_questions,
            "stage": stage,
            "final_diagnosis": top_diseases[0] if stage == "conclusion" else None,
            "diagnosis_session": session_id,
        })
