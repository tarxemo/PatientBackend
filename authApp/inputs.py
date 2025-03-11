import graphene
from graphene import InputObjectType

# Input Object for CustomUser
class CustomUserInput(InputObjectType):
    username = graphene.String(required=True)
    email = graphene.String(required=True)
    password = graphene.String(required=True)
    user_type = graphene.String()
    phone_number = graphene.String()
    address = graphene.String()
    profile_picture = graphene.String()
    date_of_birth = graphene.Date()
    is_verified = graphene.Boolean()
