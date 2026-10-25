from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import RegisterSerializer, UserSerializer


class LoginView(TokenObtainPairView):
    throttle_scope = "auth"
    throttle_classes = [ScopedRateThrottle]


class RegisterAPIView(APIView):
    """Public sign-up: anyone can create a CUSTOMER account."""

    permission_classes = [AllowAny]
    throttle_scope = "auth"
    throttle_classes = [ScopedRateThrottle]

    @extend_schema(operation_id="auth_register", request=RegisterSerializer, responses=RegisterSerializer)
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            RegisterSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    @extend_schema(operation_id="auth_me", responses=UserSerializer)
    def get(self, request):
        return Response(UserSerializer(request.user).data)
