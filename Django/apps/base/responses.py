from rest_framework.response import Response
from rest_framework import status
from django.utils.translation import gettext_lazy as _
class BaseResponse(Response):
    def __init__(self, *, data=None, status=None, message:str = None, template_name=None, headers=None, exception=False, content_type=None):
        super().__init__(data, status, template_name, headers, exception, content_type)
        if data is not None:
            self.data["message"] = message
        else:
            self.data = {"message": message}
    
    @staticmethod
    def ok(data:dict[str, object] | None = None, message:str = None) -> 'BaseResponse':
        return BaseResponse(data=data, message=message, status=status.HTTP_200_OK)
    
    @staticmethod
    def created(data:dict[str, object] | None = None, message:str = None) -> 'BaseResponse':
        message = message or _("The resource was created successfully")
        return BaseResponse(data=data, status=status.HTTP_201_CREATED, message=message)
    
    @staticmethod
    def bad_request(data:dict[str, object] | None = None, message:str = None) -> 'BaseResponse':
        message = message or _("The request was invalid or cannot be otherwise served")
        return BaseResponse(data=data, status=status.HTTP_400_BAD_REQUEST, message=message)
    
    @staticmethod
    def not_found(data:dict[str, object] | None = None, message:str = None) -> 'BaseResponse':
        message = message or _("The requested resource was not found")
        return BaseResponse(data=data, status=status.HTTP_404_NOT_FOUND, message=message)
    
    @staticmethod
    def internal_server_error(data:dict[str, object] | None = None, message:str = None) -> 'BaseResponse':
        message = message or _("An error occurred in the server")
        return BaseResponse(data=data, status=status.HTTP_500_INTERNAL_SERVER_ERROR, message=message)
    
    @staticmethod
    def not_allowed(data:dict[str, object] | None = None, message:str = None) -> 'BaseResponse':
        message = message or _("The method is not allowed for the requested URL")
        return BaseResponse(data=data, status=status.HTTP_405_METHOD_NOT_ALLOWED, message=message)
    
    @staticmethod
    def unauthorized(data:dict[str, object] | None = None, message:str = None) -> 'BaseResponse':
        message = message or _("You don't have permission to access this resource")
        return BaseResponse(data=data, status=status.HTTP_401_UNAUTHORIZED, message=message)
    
    @staticmethod
    def forbidden(data:dict[str, object] | None = None, message:str = None) -> 'BaseResponse':
        message = message or _("Forbidden")
        return BaseResponse(data=data, status=status.HTTP_403_FORBIDDEN, message=message)
    