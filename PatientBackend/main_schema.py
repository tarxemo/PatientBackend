import graphene
from authApp.views import Mutation
from authApp.schema import Query

schema = graphene.Schema(query=Query, mutation=Mutation)