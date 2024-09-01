from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as BaseTokenObtainPairSerializer

from rest_framework import serializers

from oauth.models import Profile


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        fields = ['id', 'username', 'password', 'email', 'first_name', 'last_name']

    def create(self, validated_data):
        user = super(UserCreateSerializer, self).create(validated_data)
        Profile.objects.create(user=user)
        #TODO: create default categories, subcategories, account types on first log
        return user

class TokenObtainPairSerializer(BaseTokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        profile = Profile.objects.get(user_id=self.user.id)
        serializer = ProfileSerializer(profile)
        data['email'] = self.user.email
        data['profile_id'] = serializer.data.get('id')
        data['is_premium'] = serializer.data.get('is_premium')
        return data


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'password', 'is_premium', 'user_id']

    first_name = serializers.SerializerMethodField('get_first_name')
    last_name = serializers.SerializerMethodField('get_last_name')
    password = serializers.SerializerMethodField('get_password')
    username = serializers.SerializerMethodField('get_username')
    email = serializers.SerializerMethodField('get_email')
    def get_first_name(self, obj):
        return obj.user.first_name

    def get_last_name(self, obj):
        return obj.user.last_name

    def get_password(self, obj):
        return obj.user.password

    def get_username(self, obj):
        return obj.user.username

    def get_email(self, obj):
        return obj.user.email