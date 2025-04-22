from patient.dashboard_queries import DashboardQuery
from patient.analysis_queries import PatientAnalyticsQuery
import graphene
from authApp.views import Mutation
from authApp.schema import Query
from patient.views import PatientMutation
from patient.schema import PatientQuery

class RootQuery(Query, DashboardQuery, PatientAnalyticsQuery, PatientQuery, graphene.ObjectType):
    pass

class RootMutation(Mutation, PatientMutation, graphene.ObjectType):
    pass

schema = graphene.Schema(query=RootQuery, mutation=RootMutation)
