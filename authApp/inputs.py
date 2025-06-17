import graphene
from graphene import DateTime, InputObjectType

class ProfileInput(graphene.InputObjectType):
    # Shared profile fields
    phone_number = graphene.String()
    address = graphene.String()
    profile_image = graphene.String()  # File upload handled separately via mutation or pre-upload

    # Patient-specific
    date_of_birth = DateTime()
    gender = graphene.String()  # 'Male', 'Female', 'Other'
    medical_history = graphene.String()

    # Doctor and LabTech specific
    specialization = graphene.String()
    license_number = graphene.String()
    years_of_experience = graphene.Int()
    is_available = graphene.Boolean()


class UserInput(graphene.InputObjectType):
    username = graphene.String(required=True)
    email = graphene.String(required=True)
    password = graphene.String(required=True)
    first_name = graphene.String(required=True)
    last_name = graphene.String(required=True)
    user_type = graphene.String()  # 'admin', 'doctor', 'patient', 'lab_technician'
    phone_number = graphene.String()
    address = graphene.String()
    date_of_birth = DateTime()
    is_verified = graphene.Boolean(default_value=True)
    confirm_password = graphene.String()
    is_active = graphene.Boolean(default_value=True)
    profile_data = graphene.Field(ProfileInput, required=False)


    
class ProfileInput(graphene.InputObjectType):
    specialization = graphene.String(required=False)
    license_number = graphene.String(required=False)
    years_of_experience = graphene.Int(required=False)
    is_available = graphene.Boolean(required=False)
    gender = graphene.String(required=False)
    medical_history = graphene.String(required=False)
    # Add other profile fields as needed
    
    
class UserUpdateInput(graphene.InputObjectType):
    user_id = graphene.ID(required=True)
    username = graphene.String()
    email = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()
    user_type = graphene.String()
    phone_number = graphene.String()
    address = graphene.String()
    profile_picture = graphene.String()  # Assumes you're passing a file URL or filename
    date_of_birth = DateTime()
    is_verified = graphene.Boolean()

    old_password = graphene.String()
    new_password = graphene.String()
    confirm_password = graphene.String()
    is_active = graphene.Boolean(default_value=True)
    profile_data = graphene.Field(ProfileInput, required=False)
