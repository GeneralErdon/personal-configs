from rest_framework import serializers

from apps.users.models import User
from apps.users.typing import _TUserValidatedData

class UserReadOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ("password",)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
    
    def validate_groups(self, groups:list[str]):
        if not self.instance: # if Patch
            return None
        
        return groups
    def validate_user_permissions(self, perms:list[str]):
        if not self.instance:
            return None
        
        return perms
    
    def set_user_password(self, user:User, password:str):
        user.set_password(password)
        user.save()
        return user
    
    
    def create(self, validated_data:_TUserValidatedData) -> User:
        user_created = User(**validated_data)
        user_created = self.set_user_password(user_created, validated_data["password"])
        
        return user_created
    
    def update(self, instance, validated_data:_TUserValidatedData) -> User:
        user_updated:User = super().update(instance, validated_data)
        if "password" in validated_data:
            user_updated = self.set_user_password(user_updated, validated_data["password"])
        return user_updated

