import graphene
from graphene import Mutation
from .models import *
from .inputs import *
from .outputs import *
from django.contrib.auth import authenticate
from graphql import GraphQLError
from rest_framework_simplejwt.tokens import RefreshToken


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

    def mutate(self, info):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("Not authenticated")

        # Blacklist the refresh token (if using Django SimpleJWT's token blacklist feature)
        return LogoutMutation(success=True)


# Mutation to create a new user
class CreateCustomUser(Mutation):
    class Arguments:
        user_data = CustomUserInput(required=True)

    user = graphene.Field(CustomUserOutput)

    def mutate(self, info, user_data):
        user = CustomUser.objects.create(
            username=user_data.username,
            email=user_data.email,
            # user_type=user_data.user_type,
            phone_number=user_data.phone_number,
            address=user_data.address,
            profile_picture=user_data.profile_picture,
            date_of_birth=user_data.date_of_birth,
            # is_verified=user_data.is_verified,
        )
        user.set_password(user_data.password)
        user.save()
        return CreateCustomUser(user=user)

# Mutation to update a user
class UpdateCustomUser(Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        user_data = CustomUserInput(required=True)

    user = graphene.Field(CustomUserOutput)

    def mutate(self, info, id, user_data):
        user = CustomUser.objects.get(id=id)
        for field, value in user_data.items():
            if field == "password":
                user.set_password(value)
            else:
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

class Mutation(graphene.ObjectType):
    create_user = CreateCustomUser.Field()
    update_user = UpdateCustomUser.Field()
    delete_user = DeleteCustomUser.Field()
    login = LoginMutation.Field()
    refresh_token = RefreshTokenMutation.Field()
    logout = LogoutMutation.Field()