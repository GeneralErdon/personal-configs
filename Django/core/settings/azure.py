"""
                    _                      
                   / \    _____   _ _ __ ___
                  / _ \  |_  / | | | '__/ _ \
                 / ___ \  / /| |_| | | |  __/
                /_/   \_\/___|\__,_|_|  \___|
                                             
This file contains the configuration for Azure Storage integration.

It sets up Azure Blob Storage as the storage backend for static and media files in production:

- DEFAULT_FILE_STORAGE and STATICFILES_STORAGE are set to use Azure Storage.
- Azure account details and container information are configured.
- STATIC_URL and MEDIA_URL are updated to use the Azure CDN.

These settings are only applied when DEBUG is False (i.e., in production).
Ensure all necessary environment variables are set in your production environment.
"""

from .base import env, DEBUG

# OAuth configuration
# Configure django to redirect users to the right URL for login
# LOGIN_URL = "django_auth_adfs:login"
# LOGIN_REDIRECT_URL = "/"

AZURE_CLIENT_ID = env.str("AZURE_OAUTH_CLIENT_ID")
AZURE_CLIENT_SECRET = env.str("AZURE_OAUTH_SECRET")
AZURE_TENANT_ID = env.str("AZURE_TENANT_ID")
AZURE_REDIRECT_URI = env.str("AZURE_REDIRECT_URI", "http://localhost:2526/api/v1/oauth2/callback")


# AUTH_ADFS = {
#     "AUDIENCE": AZURE_CLIENT_ID,
#     "CLIENT_ID": AZURE_CLIENT_ID,
#     "CLIENT_SECRET": AZURE_CLIENT_SECRET,
#     'LOGIN_EXEMPT_URLS': [
#         '^api',  # Assuming you API is available at /api
#     ],
#     "RELYING_PARTY_ID": AZURE_CLIENT_ID,
# }
# OAUTH2_PROVIDER = {
#     'SCOPES': {'read': 'Read scope', 'write': 'Write scope'},
#     'ACCESS_TOKEN_EXPIRE_SECONDS': 3600,  # 1 hora
#     'OAUTH2_BACKEND_CLASS': 'oauth2_provider.oauth2_backends.JSONOAuthLibCore',
# }

# # Configuración de Azure AD
# AZURE_AD = {
#     'TENANT_ID': AZURE_TENANT_ID,  # Reemplaza con tu Tenant ID de Azure
#     'CLIENT_ID': AZURE_CLIENT_ID,
#     'CLIENT_SECRET': AZURE_CLIENT_SECRET,
#     # 'RESOURCE': 'https://graph.microsoft.com',  # O el recurso que necesites
# }

if not DEBUG:
    # Configuración de Azure Storage
    DEFAULT_FILE_STORAGE = 'storages.backends.azure_storage.AzureStorage'
    STATICFILES_STORAGE = 'storages.backends.azure_storage.AzureStorage'
    
    AZURE_ACCOUNT_NAME = env.str("AZURE_STORAGE_ACCOUNT_NAME")
    AZURE_ACCOUNT_KEY = env.str("AZURE_STORAGE_ACCOUNT_KEY")
    AZURE_CONTAINER = env.str("AZURE_STORAGE_CONTAINER_NAME")
    AZURE_CUSTOM_DOMAIN = f'{AZURE_ACCOUNT_NAME}.blob.core.windows.net'
    
    STATIC_URL = f'https://{AZURE_CUSTOM_DOMAIN}/{AZURE_CONTAINER}/'
    MEDIA_URL = f'https://{AZURE_CUSTOM_DOMAIN}/{AZURE_CONTAINER}/'

    # Elimina estas líneas si no las necesitas
    # AZURE_LOCATION = env.str("AZURE_STORAGE_LOCATION")
    # AZURE_SAS_TOKEN = env.str("AZURE_STORAGE_SAS_TOKEN")
    # AZURE_CONNECTION_STRING = env.str("AZURE_STORAGE_CONNECTION_STRING")