from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Collection,
    CollectionRecord,
    CustomUser,
    Flower,
    FlowerSubmission,
    Temple,
)


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = CustomUser
        fields = ["id", "full_name", "email", "phone", "role", "role_display", "is_active", "created_at"]
        read_only_fields = ["id", "role_display", "created_at"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ["id", "full_name", "email", "phone", "role", "password", "confirm_password"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("confirm_password"):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(email=attrs["email"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("Account is inactive. Please contact administration.")
        refresh = RefreshToken.for_user(user)
        return {
            "user": UserSerializer(user).data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }


class TempleSerializer(serializers.ModelSerializer):
    owner_details = UserSerializer(source="owner", read_only=True)

    class Meta:
        model = Temple
        fields = ["id", "name", "city", "state", "address", "contact_number", "contact_person", "owner", "owner_details", "created_at"]


class FlowerSubmissionSerializer(serializers.ModelSerializer):
    temple_name = serializers.CharField(source="temple.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    submitted_by_name = serializers.CharField(source="submitted_by.full_name", read_only=True)

    class Meta:
        model = FlowerSubmission
        fields = [
            "id",
            "temple",
            "temple_name",
            "submitted_by",
            "submitted_by_name",
            "flower_type",
            "weight",
            "submission_date",
            "remarks",
            "status",
            "status_display",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "temple_name", "status_display", "submitted_by_name", "created_at", "updated_at"]

    def validate_weight(self, value):
        if value <= 0:
            raise serializers.ValidationError("Flower weight must be strictly greater than 0 kg.")
        return value


class CollectionRecordSerializer(serializers.ModelSerializer):
    submission_details = FlowerSubmissionSerializer(source="submission", read_only=True)
    collector_name = serializers.CharField(source="collector.full_name", read_only=True)

    class Meta:
        model = CollectionRecord
        fields = [
            "id",
            "submission",
            "submission_details",
            "collector",
            "collector_name",
            "collected_at",
            "collected_weight",
            "remarks",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "submission_details", "collector_name", "created_at"]

    def validate_collected_weight(self, value):
        if value <= 0:
            raise serializers.ValidationError("Collected weight must be strictly greater than 0 kg.")
        return value


class FlowerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flower
        fields = "__all__"
