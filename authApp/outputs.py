import graphene
from graphene import ObjectType, DateTime, Decimal, UUID
from .models import *

# Output Object for CustomUser
class CustomUserOutput(ObjectType):
    id = graphene.ID()
    username = graphene.String()

    first_name =graphene.String()
    last_name = graphene.String()
    email = graphene.String()
    user_type = graphene.String()
    phone_number = graphene.String()
    address = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()
    profile_picture = graphene.String()
    date_of_birth = graphene.Date()
    is_verified = graphene.Boolean()
    created_at = DateTime()
    updated_at = DateTime()
    
    is_active = graphene.Boolean()
