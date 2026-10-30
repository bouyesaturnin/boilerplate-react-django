from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("email", "username", "password")

    def validate(self, attrs):
        # Validateurs AUTH_PASSWORD_VALIDATORS appliqués avec l'utilisateur en cours de création :
        # UserAttributeSimilarityValidator peut ainsi comparer le mot de passe à l'email et au username.
        candidate = User(email=attrs.get("email"), username=attrs.get("username"))
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "username", "first_name", "last_name", "date_joined")
        read_only_fields = ("id", "email", "date_joined")
