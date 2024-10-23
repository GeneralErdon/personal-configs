from rest_framework.authentication import BasicAuthentication, TokenAuthentication, BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils.translation import gettext_lazy as _
from apps.base.oauth.utils import AzureOAuthUtils
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.backends import ModelBackend
from django.shortcuts import redirect
from django.conf import settings
from django.urls import reverse
from urllib.parse import urlencode
from apps.users.models import User

class AzureSwaggerAuthentication(JWTAuthentication): 
    def authenticate(self, request):
        """This custom authentication is used to authenticate the user using the token JWT generated by
        my backend after azure login.

        Args:
            request (Request): The request object.

        Raises:
            AuthenticationFailed: If the token is invalid.

        Returns:
            Tuple[User, None]: A tuple containing the user and None.
        """
        token = request.query_params.get('token')
        if not token:
            return None
        
        validated_token = self.get_validated_token(token.encode())
        
        try:
            user = User.objects.filter(id=validated_token["user_id"]).first()
            if user is None:
                raise AuthenticationFailed(_("User not found"))
        except KeyError:
            raise AuthenticationFailed(_("Invalid token"))
        except Exception as e:
            raise AuthenticationFailed(_("Invalid token"))
        
        return (user, None)

class AzureAdminAuthentication(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Si ya tenemos un token en la sesión, usamos eso para autenticar
        if request.session.get('azure_access_token'):
            email = request.session.get('azure_user_email')
            if email:
                try:
                    return User.objects.get(email=email)
                except User.DoesNotExist:
                    return None
        
        # Si no tenemos un token, redirigimos al login de Azure
        params = {
            'client_id': settings.AZURE_CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': request.build_absolute_uri('/admin/azure-callback/'),
            'scope': 'openid profile email',
            'response_mode': 'query'
        }
        azure_login_url = f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/oauth2/v2.0/authorize?{urlencode(params)}"
        return redirect(azure_login_url)

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None