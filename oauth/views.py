import base64

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import RetrieveModelMixin, CreateModelMixin, UpdateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.views import TokenObtainPairView as BaseTokenObtainPairView

from oauth.models import Profile
from oauth.serializers import ProfileSerializer, TokenObtainPairSerializer


class ProfileViewSet(CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    queryset = Profile.objects.select_related('user').all()
    serializer_class = ProfileSerializer

    @action(detail=False, methods=['GET', 'PUT'])
    def me(self, request):
        if request.method == 'GET':
            profile, _ = Profile.objects.select_related('user').get_or_create(user_id=request.user.id)
            serializer = ProfileSerializer(profile)
            return Response(serializer.data)
        elif request.method == 'PUT':
            profile, _ = Profile.objects.select_related('user').get_or_create(user_id=request.user.id)
            serializer = ProfileSerializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)


class TokenObtainPairView(BaseTokenObtainPairView):
    serializer_class = TokenObtainPairSerializer


class PasswordResetWithoutEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        from django.conf import settings
        if not settings.DEBUG and not getattr(request.user, 'is_staff', False):
            return Response(
                {"error": "Password reset without email verification is disabled in production."},
                status=status.HTTP_403_FORBIDDEN
            )
        identifier = request.data.get('username')
        User = get_user_model()
        try:
            user = User.objects.get(username=identifier)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        uid = base64.urlsafe_b64encode(str(user.pk).encode())
        token = default_token_generator.make_token(user)

        return Response({
            "uid": uid,
            "token": token
        }, status=status.HTTP_200_OK)

