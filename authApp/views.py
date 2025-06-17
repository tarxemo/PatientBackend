from contextvars import Token
import uuid
from patient.utils import handle_user_profile
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
from authApp.inputs import *

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
from patient.models import Disease, Patient  # Assuming Disease model exists


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
            patient = Patient.objects.create(
                user = user
            )
            patient.save()
            
            return CreateUser(user=user)
            
        except Exception as e:
            raise GraphQLError(f"User creation failed: {str(e)}")
        
class CreateCustomUser(Mutation):
    class Arguments:
        user_data = UserInput(required=True)
    
    user = graphene.Field(CustomUserOutput)
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, user_data):
        try:
            # Create the base user
            user = CustomUser.objects.create_user(
                username=user_data.username,
                email=user_data.email,
                password=user_data.password,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                user_type=user_data.user_type,
                phone_number=user_data.phone_number,
                address=user_data.address,
                date_of_birth=user_data.date_of_birth,
                is_verified=user_data.is_verified if hasattr(user_data, 'is_verified') else False
            )
            
            # Handle profile creation
            handle_user_profile(user, user_data.user_type, user_data.profile_data)
            
            return CreateCustomUser(user=user, success=True, message="Ready")
        except Exception as e:
            raise GraphQLError(f"User creation failed: {str(e)}")
        
        
class UpdateCustomUser(Mutation):
    class Arguments:
        user_data = UserUpdateInput(required=True)
        profile_data = ProfileInput(required=False)
    
    user = graphene.Field(CustomUserOutput)

    def mutate(self, info, user_data, profile_data=None):
        try:
            # Get user by provided ID
            user = CustomUser.objects.get(id=user_data.user_id)
            old_user_type = user.user_type

            # Handle password update if provided
            if user_data.old_password and user_data.new_password:
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
            
            # Handle profile changes if user_type changed or profile_data provided
            if (hasattr(user_data, 'user_type') and user_data.user_type != old_user_type) or profile_data:
                handle_user_profile(user, user.user_type, profile_data)
            
            return UpdateCustomUser(user=user)

        except CustomUser.DoesNotExist:
            raise GraphQLError("User not found")
        except Exception as e:
            raise GraphQLError(f"Update failed: {str(e)}")

class DeleteUser(Mutation):
    class Arguments:
        user_id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
            
            # Delete the associated profile based on user type
            if user.user_type == 'doctor' and hasattr(user, 'doctor_profile'):
                user.doctor_profile.delete()
            elif user.user_type == 'patient' and hasattr(user, 'patient_profile'):
                user.patient_profile.delete()
            elif user.user_type == 'lab_technician' and hasattr(user, 'labtech_profile'):
                user.labtech_profile.delete()
            
            # Delete the user
            user.delete()
            
            return DeleteUser(success=True, message="User deleted successfully")
        except CustomUser.DoesNotExist:
            raise GraphQLError("User not found")
        except Exception as e:
            raise GraphQLError(f"Failed to delete user: {str(e)}")
          


class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    admin_create_user = CreateCustomUser.Field()
    admin_update_user = UpdateCustomUser.Field()
    admin_delete_user = DeleteUser.Field()
    login = LoginMutation.Field()
    refresh_token = RefreshTokenMutation.Field()
    logout = LogoutMutation.Field()
    
    
import os
import shutil
import subprocess
import json
import joblib
import whisper
import numpy as np
import uuid
from django.conf import settings
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.views import APIView
from patient.models import Disease, Symptom
from .tokenizer_utils import syllable_tokenizer
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
#whisper_model = whisper.load_model("large")

# Load disease prediction model and necessary files
disease_model = joblib.load("swahili_disease_predictor_syllable.pkl")
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



    def post(self, request, *args, **kwargs):
        if 'question_id' in request.data:
            return self.handle_follow_up(request)
        return self.handle_initial_request(request)

    def handle_initial_request(self, request):
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
            transcription_result = whisper_model.transcribe(converted_audio, language="swahili")
            transcribed_text = transcription_result["text"]
        else:
            transcribed_text=symptoms_text # Return error if any

        # Get initial prediction
        # try:
        prediction = disease_model.predict_proba([transcribed_text])[0]
        classes = disease_model.classes_
        
        # Get top predictions
        top_indices = np.argsort(prediction)[::-1][:3]
        top_predictions = classes[top_indices]
        top_probabilities = prediction[top_indices] * 100
        print(top_probabilities)
        # Create diagnostic session
        session_id = str(uuid.uuid4())
        diagnosis_state = {
            'transcribed_text': transcribed_text,
            'current_predictions': top_predictions.tolist(),
            'current_probabilities': top_probabilities.tolist(),
            'asked_questions': [],
            'user_responses': {},
            'interaction_count': 0,
            'diagnosis_stage': 'initial'
        }
        print(request.user.username)
        cache.set(f'diagnosis_{request.user.username}', diagnosis_state, timeout=3600)

        # Generate first set of questions
        questions = self.generate_next_questions(
            top_predictions, 
            diagnosis_state
        )

        return Response({
            "transcript": transcribed_text,
            "predicted_diseases": self.format_disease_info(top_predictions, top_probabilities),
            "questions": questions,
            "diagnosis_session": session_id,
            "stage": "followup" if len(questions) > 0 else "conclusion"
        })

        # except Exception as e:
        #     return Response(
        #         {"error": f"Prediction failed: {str(e)}"}, 
        #         status=status.HTTP_500_INTERNAL_SERVER_ERROR
        #     )

    def handle_follow_up(self, request):
        """Handle follow-up interactions"""
        session_id = request.data.get('diagnosis_session')
        if not session_id:
            return Response({"error": "Missing diagnosis session"}, status=400)
        
        diagnosis_state = cache.get(f'diagnosis_{request.user.username}')
        if not diagnosis_state:
            return Response({"error": "Session expired or invalid"}, status=400)

        # Store user response
        question_id = request.data.get('question_id')
        response = request.data.get('response')
        
        diagnosis_state['user_responses'][str(question_id)] = response
        diagnosis_state['asked_questions'].append(question_id)
        diagnosis_state['interaction_count'] += 1

        # Update probabilities based on responses
        updated_probs = self.update_probabilities(
            diagnosis_state['current_predictions'],
            diagnosis_state['user_responses'],
            diagnosis_state['transcribed_text']
        )

        # Sort diseases by updated probabilities
        sorted_diseases = sorted(
            updated_probs.items(),
            key=lambda x: -x[1]
        )
        top_diseases = [d[0] for d in sorted_diseases]
        
        # Update diagnosis state
        diagnosis_state['current_predictions'] = top_diseases
        diagnosis_state['current_probabilities'] = [d[1] for d in sorted_diseases]
        
        # Determine if we should conclude
        should_conclude = (
            diagnosis_state['interaction_count'] >= 6 or
            not self.has_differentiating_questions(top_diseases, diagnosis_state)
        )

        if should_conclude:
            diagnosis_state['diagnosis_stage'] = 'conclusion'
            questions = []
            stage = "conclusion"
        else:
            questions = self.generate_next_questions(
                top_diseases,
                diagnosis_state
            )
            stage = "followup"

        cache.set(f'diagnosis_{request.user.username}', diagnosis_state, timeout=3600)

        return Response({
            "predicted_diseases": self.format_disease_info(top_diseases, [d[1] for d in sorted_diseases]),
            "questions": questions,
            "stage": stage,
            "final_diagnosis": sorted_diseases[0][0] if stage == "conclusion" else None,
            "diagnosis_session": session_id,
            "interaction_count": diagnosis_state['interaction_count']
        })

    def generate_next_questions(self, diseases, diagnosis_state):
        """Generate the most relevant next questions based on current probabilities and history"""
        asked_question_ids = diagnosis_state['asked_questions']
        current_probs = diagnosis_state['current_probabilities']
        previous_responses = diagnosis_state['user_responses']
        
        diseases_qs = Disease.objects.filter(name__in=diseases)
        all_symptoms = Symptom.objects.filter(
            related_diseases__in=diseases_qs
        ).exclude(
            id__in=asked_question_ids
        ).distinct()

        # Calculate symptom importance scores with multiple factors
        symptom_scores = []
        for symptom in all_symptoms:
            score = self.calculate_dynamic_symptom_score(
                symptom, 
                diseases_qs,
                current_probs,
                previous_responses,
                diagnosis_state['interaction_count']
            )
            symptom_scores.append((symptom, score))
        
        # Sort by highest diagnostic value
        symptom_scores.sort(key=lambda x: -x[1])
        
        # Select questions using adaptive strategy
        questions = self.select_adaptive_questions(
            symptom_scores,
            diseases_qs,
            current_probs,
            diagnosis_state['interaction_count']
        )
        
        return questions

    def calculate_dynamic_symptom_score(self, symptom, diseases_qs, current_probs, previous_responses, interaction_count):
        """Calculate symptom importance using multiple dynamic factors"""
        # Get current probabilities by disease
        disease_probs = {d.name: p for d, p in zip(diseases_qs, current_probs)}
        top_disease = max(disease_probs.items(), key=lambda x: x[1])
        
        # Which diseases have this symptom
        positive_diseases = diseases_qs.filter(related_symptoms=symptom)
        positive_names = [d.name for d in positive_diseases]
        is_top_disease_symptom = top_disease[0] in positive_names
        
        # Calculate probability mass for symptom presence
        prob_if_present = sum(p for d, p in disease_probs.items() if d in positive_names)
        prob_if_absent = 1 - prob_if_present
        
        # 1. CONFIRMATION VALUE (how much it confirms top diagnosis)
        confirmation_score = 0
        if is_top_disease_symptom:
            # Base confirmation value weighted by disease probability
            confirmation_score = top_disease[1] * 0.6
            
            # Boost if we've had confirming responses to similar symptoms
            similar_confirmed = self.get_similar_symptom_confirmation(symptom, positive_names, previous_responses)
            confirmation_score *= (1 + 0.3 * similar_confirmed)
        
        # 2. ELIMINATION VALUE (how much it could rule out alternatives)
        elimination_score = 0
        if not is_top_disease_symptom:
            # Value is proportional to how much it would reduce non-top diseases
            elimination_score = (1 - top_disease[1]) * 0.7
            
            # Boost if we've had eliminating responses to similar symptoms
            similar_eliminated = self.get_similar_symptom_elimination(symptom, positive_names, previous_responses)
            elimination_score *= (1 + 0.2 * similar_eliminated)
        
        # 3. INFORMATION GAIN (how much it changes the probability distribution)
        info_gain = 1 - abs(prob_if_present - prob_if_absent)
        
        # 4. INTERACTION WEIGHTING (earlier interactions matter more)
        interaction_weight = 1.5 - (0.2 * interaction_count)  # Decreases with each interaction
        
        # Combine scores with weights
        total_score = (
            (confirmation_score * 0.5) +
            (elimination_score * 0.3) + 
            (info_gain * 0.2)
        ) * interaction_weight
        
        # Penalize symptoms that are common to all remaining diseases
        if len(positive_names) == len(disease_probs):
            total_score *= 0.2  # Much less valuable
        
        return total_score

    def get_similar_symptom_confirmation(self, symptom, positive_names, previous_responses):
        """Check if similar symptoms from same diseases were confirmed"""
        count = 0
        for q_id, response in previous_responses.items():
            if response:  # Only count positive responses
                prev_symptom = Symptom.objects.get(id=q_id)
                prev_diseases = [d.name for d in prev_symptom.related_diseases.all()]
                # Check if any overlapping diseases
                if any(d in positive_names for d in prev_diseases):
                    count += 1
        return min(count, 3) / 3  # Normalize to 0-1 range

    def get_similar_symptom_elimination(self, symptom, positive_names, previous_responses):
        """Check if similar symptoms from other diseases were denied"""
        count = 0
        for q_id, response in previous_responses.items():
            if not response:  # Only count negative responses
                prev_symptom = Symptom.objects.get(id=q_id)
                prev_diseases = [d.name for d in prev_symptom.related_diseases.all()]
                # Check if any non-overlapping diseases
                if not any(d in positive_names for d in prev_diseases):
                    count += 1
        return min(count, 3) / 3  # Normalize to 0-1 range

    def select_adaptive_questions(self, symptom_scores, diseases_qs, current_probs, interaction_count):
        """Intelligently select questions based on current diagnostic state"""
        top_disease = diseases_qs[int(np.argmax(current_probs))]
        top_prob = max(current_probs)
        
        # Categorize symptoms
        top_disease_symptoms = []
        other_symptoms = []
        
        for symptom, score in symptom_scores:
            if top_disease in symptom.related_diseases.all():
                top_disease_symptoms.append((symptom, score))
            else:
                other_symptoms.append((symptom, score))
        
        # Determine question mix based on confidence level
        if top_prob > 80:  # Very confident - focus on confirmation
            questions = top_disease_symptoms[:2]
            if len(questions) < 2 and other_symptoms:
                questions.append(other_symptoms[0])
        elif top_prob > 60:  # Somewhat confident - balanced approach
            questions = top_disease_symptoms[:1] + other_symptoms[:1]
            if len(questions) < 2 and (top_disease_symptoms or other_symptoms):
                questions.append((top_disease_symptoms + other_symptoms)[0])
        else:  # Not confident - focus on differentiation
            questions = other_symptoms[:1] + top_disease_symptoms[:1]
        
        # Ensure we have 2-3 questions
        num_questions = min(3, max(2, 4 - interaction_count))
        if len(questions) < num_questions:
            remaining = [s for s in symptom_scores if s not in questions]
            questions.extend(remaining[:num_questions - len(questions)])
        
        return [{
            'id': s.id,
            'text': f"Je, una {s.swahili_name.lower()}? ({s.name})",
            'type': 'boolean'
        } for s, _ in questions[:num_questions]]


    def calculate_symptom_score(self, symptom, diseases_qs, current_probs):
        """Calculate how valuable knowing this symptom would be, weighted by current probabilities"""
        # Get disease probabilities as dictionary
        disease_probs = {d.name: p for d, p in zip(diseases_qs, current_probs)}
        
        # Calculate weighted score based on:
        # 1. How specific the symptom is to the most likely disease
        # 2. How much it helps differentiate between diseases
        
        # Diseases that have this symptom
        positive_diseases = diseases_qs.filter(related_symptoms=symptom)
        positive_names = [d.name for d in positive_diseases]
        
        # Calculate probability mass for diseases with this symptom
        prob_positive = sum(
            prob for disease, prob in disease_probs.items()
            if disease in positive_names
        )
        
        # Calculate information gain (how much it would change probabilities)
        # Weight by how likely the symptom is given the current probabilities
        symptom_prevalence = prob_positive
        
        # Calculate how much this symptom would help confirm the top diagnosis
        top_disease = max(disease_probs.items(), key=lambda x: x[1])
        is_top_disease_symptom = top_disease[0] in positive_names
        
        # Score components:
        # 1. High if symptom is present in top disease (weighted by disease probability)
        # 2. High if it helps differentiate between diseases (information gain)
        # 3. Weighted by how likely the symptom is given current probabilities
        
        if is_top_disease_symptom:
            # Strong preference for symptoms of the most likely disease
            confirmation_score = top_disease[1] * 0.7  # 70% weight to confirming top diagnosis
            differentiation_score = (1 - abs(prob_positive - (1 - prob_positive))) * 0.3
            return confirmation_score + differentiation_score
        else:
            # For symptoms not in top disease, only consider differentiation value
            return (1 - abs(prob_positive - (1 - prob_positive))) * 0.3  # Reduced weight

    def update_probabilities(self, diseases, user_responses, original_text):
        """Update disease probabilities based on user responses"""
        diseases_qs = Disease.objects.filter(name__in=diseases)
        
        # Get base probabilities from model
        base_probs = disease_model.predict_proba([original_text])[0]
        prob_dict = {
            disease: base_probs[np.where(disease_model.classes_ == disease)[0][0]] * 100
            for disease in diseases
        }
        
        # Adjust based on user responses
        for symptom_id, response in user_responses.items():
            symptom = Symptom.objects.get(id=symptom_id)
            
            for disease in diseases_qs:
                has_symptom = disease.related_symptoms.filter(id=symptom.id).exists()
                
                # Stronger adjustment for early interactions
                adjustment_factor = 1.8 if len(user_responses) < 3 else 1.3
                
                if (response and has_symptom) or (not response and not has_symptom):
                    prob_dict[disease.name] *= adjustment_factor
                else:
                    prob_dict[disease.name] *= (2 - adjustment_factor)
        
        # Normalize
        total = sum(prob_dict.values())
        return {k: (v/total)*100 for k, v in prob_dict.items()}

    def has_differentiating_questions(self, diseases, diagnosis_state):
        """Check if there are still valuable questions to ask"""
        diseases_qs = Disease.objects.filter(name__in=diseases)
        asked_questions = diagnosis_state['asked_questions']
        
        remaining_symptoms = Symptom.objects.filter(
            related_diseases__in=diseases_qs
        ).exclude(
            id__in=asked_questions
        ).distinct()
        
        return remaining_symptoms.exists()

    def format_disease_info(self, diseases, probabilities):
        """Format disease information for response"""
        return [
            {
                "name": disease,
                "probability": round(prob, 2),
                "common_symptoms": self.get_common_symptoms(disease),
                "doctors": self.get_doctors(disease)
            }
            for disease, prob in zip(diseases, probabilities)
        ]

    def get_common_symptoms(self, disease_name):
        disease = Disease.objects.filter(name=disease_name).first()
        if disease:
            return [s.swahili_name for s in disease.related_symptoms.all()]
        return []

    def get_doctors(self, disease_name):
        disease = Disease.objects.filter(name=disease_name).first()
        if disease:
            return [str(d) for d in disease.doctors.all()[:3]]
        return []
