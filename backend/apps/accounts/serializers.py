from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "email", "first_name", "last_name", "role")
        read_only_fields = fields


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "email"
    default_error_messages = {
        "no_active_account": "Unable to authenticate with the provided credentials."
    }

    def validate(self, attrs):
        authenticate_kwargs = {
            "email": attrs.get("email"),
            "password": attrs.get("password"),
        }
        self.user = authenticate(**authenticate_kwargs)

        if self.user is None or not self.user.is_active:
            raise AuthenticationFailed(self.default_error_messages["no_active_account"])

        refresh = self.get_token(self.user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
