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
    print("Started but not completed")
    class Arguments:
        userData = UserInput(required=False)

    user = graphene.Field(CustomUserOutput)

    def mutate(self, info, userData):
        print(userData)
        user = CustomUser.objects.create(
            username=userData.username,
            email=userData.email
        )
        user.set_password(userData.password)
        user.save()
        return CreateUser(user=user)

# Define Mutation
class UpdateCustomUser(Mutation):
    class Arguments:
        user_data = UserUpdateInput(required=True)

    user = graphene.Field(CustomUserOutput)

    @login_required_resolver
    def mutate(self, info, user_data):
        user = CustomUser.objects.get(id=info.context.user.id)

        # Handle password update separately
        if "old_password" in user_data and "new_password" in user_data and "confirm_password" in user_data:
            old_password = user_data.pop("old_password")
            new_password = user_data.pop("new_password")
            confirm_password = user_data.pop("confirm_password")

            # Verify old password
            if not check_password(old_password, user.password):
                raise GraphQLError("Old password is incorrect.")

            # Ensure new password and confirm password match
            if new_password != confirm_password:
                raise GraphQLError("New password and confirm password do not match.")

            # Prevent using the same old password
            if check_password(new_password, user.password):
                raise GraphQLError("New password cannot be the same as the old password.")

            # Set the new password
            user.set_password(new_password)

        # Update other user details
        for field, value in user_data.items():
            setattr(user, field, value)

        user.save()
        return UpdateCustomUser(user=user)

# Mutation to delete a user
class DeleteCustomUser(Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
        user = CustomUser.objects.get(id=id)
        user.delete()
        return DeleteCustomUser(success=True)

# import os
# import subprocess
# import torch
# import whisper
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.parsers import MultiPartParser, FormParser
# from django.core.files.storage import default_storage
# from django.conf import settings
# from rest_framework import status

# # Load the Whisper model
# model_path = "whisper_large.pth"
# model = whisper.load_model("medium")

# # If a saved model exists, load it
# if os.path.exists(model_path):
#     model.load_state_dict(torch.load(model_path))
#     print("✅ Model loaded from", model_path)

# class TranscribeAudioView(APIView):
#     parser_classes = (MultiPartParser, FormParser)

#     def convert_audio_to_16khz(self, audio_path):
#         """Convert audio to 16kHz if needed."""
#         output_path = audio_path.replace(".wav", "_16k.wav")
#         if not os.path.exists(output_path):
#             command = f"ffmpeg -i {audio_path} -ar 16000 -ac 1 {output_path}"
#             subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#         return output_path

#     def post(self, request, *args, **kwargs):
#         """Handle file upload and transcription."""
#         if "audio_file" not in request.FILES:
#             return Response({"error": "No audio file provided"}, status=status.HTTP_400_BAD_REQUEST)

#         # Define the upload directory
#         upload_dir = os.path.join(settings.MEDIA_ROOT, "uploads")
#         os.makedirs(upload_dir, exist_ok=True)  # Ensure directory exists

#         # Save uploaded file
#         audio_file = request.FILES["audio_file"]
#         file_path = os.path.join(upload_dir, audio_file.name)
#         with open(file_path, "wb+") as destination:
#             for chunk in audio_file.chunks():
#                 destination.write(chunk)

#         # Convert and transcribe the audio
#         converted_audio = self.convert_audio_to_16khz(file_path)
#         result = model.transcribe(converted_audio, language="swahili")

#         return Response({"transcript": result["text"]}, status=status.HTTP_200_OK)


class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    update_user = UpdateCustomUser.Field()
    delete_user = DeleteCustomUser.Field()
    login = LoginMutation.Field()
    refresh_token = RefreshTokenMutation.Field()
    logout = LogoutMutation.Field()