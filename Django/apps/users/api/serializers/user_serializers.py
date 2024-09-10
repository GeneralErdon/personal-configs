from rest_framework import serializers

from apps.base.serializers import BaseReadOnlySerializer
from apps.users.models import User
from apps.users.typing import _TUserValidatedData

class UserReadOnlySerializer(BaseReadOnlySerializer):
    date_joined = serializers.DateTimeField(format="%d-%m-%Y %H:%M:%S")
    last_login = serializers.DateTimeField(format="%d-%m-%Y %H:%M:%S")
    class Meta:
        model = User
        exclude = ("password",)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
    
    def set_user_password(self, user:User, password:str):
        user.set_password(password)
        user.save()
        return user
    
    
    def create(self, validated_data:_TUserValidatedData) -> User:
        groups = validated_data.pop("groups", None)
        perms = validated_data.pop("user_permissions", None)
        
        user_created = User(**validated_data)
        user_created = self.set_user_password(user_created, validated_data["password"])
        
        if groups:
            user_created.groups.set(groups)
        if perms:
            user_created.user_permissions.set(perms)
        
        return user_created
    
    def update(self, instance, validated_data:_TUserValidatedData) -> User:
        user_updated:User = super().update(instance, validated_data)
        if "password" in validated_data:
            user_updated = self.set_user_password(user_updated, validated_data["password"])
        return user_updated

