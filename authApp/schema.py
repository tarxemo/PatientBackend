import graphene
from graphene import ObjectType, Field, List, String, Int, Decimal, DateTime, UUID
from .models import *
from .outputs import *
from .decorators import login_required_resolver
# Query to fetch all CustomUsers
class Query(ObjectType):
    # CustomUser Queries
    CustomUsers = List(CustomUserOutput)
    CustomUser = Field(CustomUserOutput, id=graphene.ID(required=True))

    def resolve_CustomUsers(self, info):
        return CustomUser.objects.all()

    def resolve_CustomUser(self, info, id):
        return CustomUser.objects.get(id=id)
