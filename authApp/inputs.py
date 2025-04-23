import graphene
from graphene import InputObjectType

class UserInput(InputObjectType):
    username = graphene.String(required=True)
    first_name =graphene.String()
    last_name = graphene.String()
    email = graphene.String(required=True)
    password = graphene.String(required=True)
    user_type = graphene.String()
    phone_number = graphene.String()
    address = graphene.String()
    profile_picture = graphene.String()
    date_of_birth = graphene.Date()
    is_verified = graphene.Boolean(default_value=False)  # Ensure default False


# Define Input Type
class UserUpdateInput(InputObjectType):
    username = graphene.String()
    first_name =graphene.String()
    last_name = graphene.String()
    email = graphene.String()
    user_type = graphene.String()
    phone_number = graphene.String()
    address = graphene.String()
    profile_picture = graphene.String()
    date_of_birth = graphene.Date()
    is_verified = graphene.Boolean(default_value=False)

    # Additional fields for password change
    old_password = graphene.String()
    new_password = graphene.String()
    confirm_password = graphene.String()