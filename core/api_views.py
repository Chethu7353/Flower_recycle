from django.db.models import Sum
from django.db.models.functions import TruncMonth
from rest_framework import generics, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Collection,
    CollectionRecord,
    CustomUser,
    Flower,
    FlowerSubmission,
    Temple,
)
from .permissions import IsAdminOrReadOnly
from .serializers import (
    CollectionRecordSerializer,
    FlowerSerializer,
    FlowerSubmissionSerializer,
    LoginSerializer,
    RegisterSerializer,
    TempleSerializer,
)


class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)


class TempleViewSet(viewsets.ModelViewSet):
    serializer_class = TempleSerializer
    permission_classes = [IsAdminOrReadOnly]
    queryset = Temple.objects.select_related("owner")
    filterset_fields = ["city", "state"]
    search_fields = ["name", "city", "state", "contact_person"]


class FlowerViewSet(viewsets.ModelViewSet):
    serializer_class = FlowerSerializer
    permission_classes = [IsAdminOrReadOnly]
    queryset = Flower.objects.all()
    filterset_fields = ["quality"]
    search_fields = ["name"]


class FlowerSubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = FlowerSubmissionSerializer
    permission_classes = [IsAuthenticated]
    queryset = FlowerSubmission.objects.select_related("temple", "submitted_by")
    filterset_fields = ["status", "flower_type", "submission_date", "temple"]
    search_fields = ["flower_type", "temple__name", "remarks"]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.role == CustomUser.Role.ADMIN or user.is_superuser:
            return qs
        if user.role == CustomUser.Role.TEMPLE_OWNER:
            return qs.filter(temple__owner=user)
        if user.role == CustomUser.Role.COLLECTOR:
            return qs
        return qs.none()

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user)


class CollectionRecordViewSet(viewsets.ModelViewSet):
    serializer_class = CollectionRecordSerializer
    permission_classes = [IsAuthenticated]
    queryset = CollectionRecord.objects.select_related("submission__temple", "collector")
    filterset_fields = ["status", "collector"]
    search_fields = ["submission__temple__name", "collector__full_name", "remarks"]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.role == CustomUser.Role.ADMIN or user.is_superuser:
            return qs
        if user.role == CustomUser.Role.COLLECTOR:
            return qs.filter(collector=user)
        if user.role == CustomUser.Role.TEMPLE_OWNER:
            return qs.filter(submission__temple__owner=user)
        return qs.none()


class CollectionViewSet(CollectionRecordViewSet):
    pass


class DashboardStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total_collected = (
            CollectionRecord.objects.aggregate(total=Sum("collected_weight"))["total"]
            or Collection.objects.aggregate(total=Sum("quantity"))["total"]
            or 0
        )
        return Response(
            {
                "total_temples": Temple.objects.count(),
                "total_temple_owners": CustomUser.objects.filter(role=CustomUser.Role.TEMPLE_OWNER).count(),
                "total_collectors": CustomUser.objects.filter(role=CustomUser.Role.COLLECTOR).count(),
                "total_submissions": FlowerSubmission.objects.count(),
                "pending_collections": FlowerSubmission.objects.filter(status__in=[FlowerSubmission.Status.SUBMITTED, FlowerSubmission.Status.PENDING]).count(),
                "completed_collections": CollectionRecord.objects.count(),
                "total_flower_waste_collected_kg": float(total_collected),
            }
        )
