from rest_framework.decorators import action
from rest_framework.mixins import RetrieveModelMixin, CreateModelMixin, UpdateModelMixin
from rest_framework.response import Response
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
            profile = Profile.objects.select_related('user').get(user_id=request.user.id)
            serializer = ProfileSerializer(profile)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = ProfileSerializer(Profile, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)


class TokenObtainPairView(BaseTokenObtainPairView):
    serializer_class = TokenObtainPairSerializer
