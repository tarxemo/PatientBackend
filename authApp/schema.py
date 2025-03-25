import graphene
from graphene import ObjectType, Field, List, String, Int, Decimal, DateTime, UUID
from .models import *
from .outputs import *
from .decorators import login_required_resolver
# Query to fetch all CustomUsers
class Query(ObjectType):
    # CustomUser Queries
    CustomUsers = List(CustomUserOutput)
    get_user = Field(CustomUserOutput)

    def resolve_CustomUsers(self, info):
        return CustomUser.objects.all()

    @login_required_resolver
    def resolve_get_user(self, info):
        return CustomUser.objects.get(id=info.context.user.id)
