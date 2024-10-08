from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as BaseTokenObtainPairSerializer

from rest_framework import serializers

from oauth.models import Profile


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        fields = ['id', 'username', 'password', 'email', 'first_name', 'last_name']

    def create(self, validated_data):
        # create profile record when create a new user
        user = super(UserCreateSerializer, self).create(validated_data)
        Profile.objects.create(user=user)
        return user


class TokenObtainPairSerializer(BaseTokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        profile = Profile.objects.get(user_id=user.id)
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['is_premium'] = profile.is_premium
        token['profile_id'] = profile.id
        return token
    def validate(self, attrs):
        data = super().validate(attrs)
        profile = Profile.objects.get(user_id=self.user.id)
        if profile:
            return {'token': data['access'], 'refresh': data['refresh']}
        else:
            return {'token': None, 'refresh': None,}


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'onboarding', 'is_premium', 'premium_plan',
                  'user_id', 'profile_picture', 'is_verified', 'two_factor_enabled', 'theme', 'language']

    first_name = serializers.SerializerMethodField('get_first_name')
    last_name = serializers.SerializerMethodField('get_last_name')
    username = serializers.SerializerMethodField('get_username')
    email = serializers.SerializerMethodField('get_email')

    def get_first_name(self, obj):
        return obj.user.first_name

    def get_last_name(self, obj):
        return obj.user.last_name

    def get_username(self, obj):
        return obj.user.username

    def get_email(self, obj):
        return obj.user.email
