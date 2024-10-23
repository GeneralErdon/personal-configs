from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.inspectors import SwaggerAutoSchema
from drf_yasg.inspectors.base import call_view_method
from drf_yasg.utils import no_body
from drf_yasg import openapi
from rest_framework.serializers import Serializer
from rest_framework import status
from apps.base.viewsets.viewsets_generics import BaseModelViewset, BaseReadOnlyViewset



class BaseSwaggerAutoSchema(SwaggerAutoSchema):
    
    def get_response_status_code(self):
        return status.HTTP_201_CREATED if self.method.lower() == 'post' else status.HTTP_200_OK
    
    
    
    
    def get_response_serializers(self):
        responses =  super().get_response_serializers()
        
        responses[str(status.HTTP_400_BAD_REQUEST)] = openapi.Response(
            description="Error de bad request",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(type=openapi.TYPE_STRING),
                    "detail": openapi.Schema(type=openapi.TYPE_ARRAY, items=[openapi.TYPE_STRING])
                },
                required=["message"],
            )
        )
        
        responses[str(status.HTTP_404_NOT_FOUND)] = openapi.Response(
            description="Error not found",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        )
        
        return responses
    
    def get_default_response_serializer(self):
        """Return the default response serializer for this endpoint. This is derived from either the ``request_body``
        override or the request serializer (:meth:`.get_view_serializer`).

        :return: response serializer, :class:`.Schema`, :class:`.SchemaRef`, ``None``
        """
        body_override = self._get_request_body_override()
        if body_override and body_override is not no_body:
            return body_override

        return self.get_readonly_serializer()
    
    
    def get_readonly_serializer(self) -> Serializer:
        return call_view_method(self.view, "get_readonly_serializer", default=self.get_view_serializer())
    
    def get_update_serializer(self) -> Serializer:
        return call_view_method(self.view, "get_update_serializer", default=self.get_view_serializer())
    
    def get_request_serializer(self):
        """Return the request serializer (used for parsing the request payload) for this endpoint.

        :return: the request serializer, or one of :class:`.Schema`, :class:`.SchemaRef`, ``None``
        :rtype: rest_framework.serializers.Serializer
        """
        body_override = self._get_request_body_override()

        if body_override is None and self.method in self.implicit_body_methods:
            # Sobreescritura, si es PATCH o UPDATE
            if self.method.upper() in ["PUT", "PATCH"]:
                return self.get_update_serializer()
            
            return self.get_view_serializer()

        if body_override is no_body:
            return None

        return body_override
    def get_operation_id(self, operation_keys):
        """
        Genera un ID de operación más legible para la documentación de Redoc.
        """
        # Obtenemos el nombre del modelo (asumimos que es la penúltima clave)
        model_name = operation_keys[-2].capitalize()
        
        # Obtenemos la acción (última clave)
        action = operation_keys[-1]
        
        # Mapeamos las acciones a nombres más legibles
        action_mapping = {
            'list': 'List',
            'create': 'Create',
            'retrieve': 'Get',
            'update': 'Update',
            'partial_update': 'Partial Update',
            'destroy': 'Delete'
        }
        
        readable_action = action_mapping.get(action, action.capitalize())
        
        # Construimos el ID de operación
        operation_id = f"{model_name} {readable_action}"
        
        return operation_id
class CustomSchemaGenerator(OpenAPISchemaGenerator):
    pass