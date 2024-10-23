from django.conf import settings
import requests
from ...users.typing import _TAzureUserInfo
from apps.users.models import User
class AzureOAuthUtils:
    """
    This class is used to handle the Azure OAuth2 login and utils
    """
    
    @staticmethod
    def get_microsoft_login_url(redirect_uri: str | None = None) -> str:
        """This method is used to get the Microsoft login URL

        Args:
            redirect_uri (str | None, optional): The redirect URI. Defaults to None.

        Returns:
            str: The Microsoft login URL
        """
        client_id = settings.AZURE_CLIENT_ID    
        tenant_id = settings.AZURE_TENANT_ID
        redirect_uri = redirect_uri or settings.AZURE_REDIRECT_URI
        return (f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"
                f"?client_id={client_id}"
                f"&response_type=code"
                f"&redirect_uri={redirect_uri}"
                f"&response_mode=query"
                f"&scope=openid profile email"
                f"&state=12345")
    
    @staticmethod
    def get_user(access_token: str) -> User | None:
        user_info = AzureOAuthUtils.get_azure_user_info(access_token)
        if not user_info:
            return None
        
        user = User.objects.filter(email=user_info['userPrincipalName'].lower(), is_active=True).first()
        return user
    
    @staticmethod
    def get_azure_user_info(access_token: str) -> _TAzureUserInfo | dict:
        user_info_url = "https://graph.microsoft.com/v1.0/me"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(user_info_url, headers=headers)
        response.raise_for_status()
        return response.json()
    
    @staticmethod
    def get_azure_token(code: str, redirect_uri: str | None = None) -> dict:
        """This method is used to get the access token from Azure

        Args:
            code (str): The code from the Azure login OAuth, received from the frontend

        Returns:
            dict: The access token from Azure
        """
        token_url = f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/oauth2/v2.0/token"
        data = {
            "client_id": settings.AZURE_CLIENT_ID,
            "client_secret": settings.AZURE_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri or settings.AZURE_REDIRECT_URI,
            "scope": "openid profile email",
        }
        response = requests.post(token_url, data=data)
        return response.json()