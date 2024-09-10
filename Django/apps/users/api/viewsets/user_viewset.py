from django.http import HttpRequest
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from apps.base.message_broker.rabbitmq_manager import RabbitMQManager
from apps.base.openapi import BaseSwaggerAutoSchema
from apps.base.viewsets.viewsets_generics import GenericModelViewset
from apps.base.viewsets.viewset_mixins import ReportViewMixin
from apps.users.api.serializers.user_serializers import UserReadOnlySerializer, UserSerializer
from apps.users.models import User, ADMINISTRATIVE_ROLE
from drf_yasg.utils import swagger_auto_schema


class UserModelViewset(ReportViewMixin, GenericModelViewset):
    serializer_class = UserSerializer
    read_only_serializer = UserReadOnlySerializer
    search_fields = [
        "username",
        "first_name",
        "last_name",
    ]
    
    
    prefetch_related_fields = [
        "groups",
        "user_permissions",
    ]
    
    
    def get_status_field(self) -> str:
        return "is_active"
    
    
    def has_admin_perms(self, user:User):
        return user.is_superuser or user.role == ADMINISTRATIVE_ROLE
    
    
    def create(self, request: Request, *args, **kwargs):
        if self.has_admin_perms(request.user):
            response:Response =  super().create(request, *args, **kwargs)
            data:dict = response.data
            # Si se crea un usuario, se guarda en la cola.
            if (response.status_code == status.HTTP_201_CREATED):
                # Quedaría el nombre de cola "user-queue"
                mq_manager = RabbitMQManager()
                
                mq_manager.publish(
                    "user.create", 
                    {
                        "id":data["id"],
                        "username":data["username"],
                        "role": data["role"]
                    },
                )
                
                mq_manager.close()
                
            
            return response

        return Response(
                {"message":"You haven't permission for this"},
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    def update(self, request: HttpRequest, pk: str, *args, **kwargs):
        if self.has_admin_perms(request.user):
            return super().update(request, pk, *args, **kwargs)
        return Response(
                {"message":"You haven't permission for this"},
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    def destroy(self, request: HttpRequest, pk: str, *args, **kwargs):
        if self.has_admin_perms(request.user):
            response =  super().destroy(request, pk, *args, **kwargs)
            if response.status_code == status.HTTP_200_OK:
                rabbit_manager = RabbitMQManager()
                rabbit_manager.delete_queue_data("user-queue", int(pk))
                rabbit_manager.close()
            return response
        return Response(
                {"message":"You haven't permission for this"},
                status=status.HTTP_401_UNAUTHORIZED
            )
    