"""
                 ____  ____  _____ 
                |  _ \|  _ \|  ___|
                | | | | |_) | |_   
                | |_| |  _ <|  _|  
                |____/|_| \_\_|    
                                   
This file contains the configuration for Django Rest Framework (DRF).

It defines different settings for development and production environments:

- DEFAULT_AUTHENTICATION_CLASSES: Specifies JWT as the authentication method.
- DEFAULT_PERMISSION_CLASSES: Sets up permissions (more restrictive in production).
- DEFAULT_FILTER_BACKENDS: Configures filtering and ordering capabilities.

Adjust these settings based on your API's authentication, authorization, and functionality requirements.
"""

from .base import DEBUG
LOGIN_URL = "/admin/login/"
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        # 'django_auth_adfs.rest_framework.AdfsAccessTokenAuthentication',
        # 'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        # 'rest_framework.permissions.IsAuthenticated',
        # 'rest_framework.permissions.DjangoModelPermissions'
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    )
}

if not DEBUG:
    REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
        'rest_framework.permissions.DjangoModelPermissions'
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
        )
    }