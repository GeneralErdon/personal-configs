"""
                 ____                                       
                / ___|_      ____ _  __ _  __ _  ___ _ __   
                \___ \ \ /\ / / _` |/ _` |/ _` |/ _ \ '__|  
                 ___) \ V  V / (_| | (_| | (_| |  __/ |     
                |____/ \_/\_/ \__,_|\__, |\__, |\___|_|     
                                    |___/ |___/             

This file contains the configuration for Swagger (OpenAPI) documentation.

It defines settings that control the behavior and appearance of the Swagger UI:

- DOC_EXPANSION: Controls how the documentation is initially displayed.
- DEFAULT_AUTO_SCHEMA_CLASS: Specifies a custom schema class for additional control over the generated documentation.

Adjust these settings to customize how your API documentation is presented and generated.
"""
from django.conf import settings


SWAGGER_SETTINGS = {
    'DOC_EXPANSION': 'none',
    'DEFAULT_AUTO_SCHEMA_CLASS': 'apps.base.openapi.BaseSwaggerAutoSchema',
    'USE_SESSION_AUTH': False,
    # 'SECURITY_DEFINITIONS': {
    #     'Azure Swagger': {
    #         'type': 'apiKey',
    #         'authorizationUrl': '/api/v1/oauth2/callback/',
    #         'name': 'token',
    #         'in': 'query',
    #     }
    # },
    # 'OAUTH2_CONFIG': {
    #     'clientId': settings.AZURE_CLIENT_ID,
    #     'clientSecret': settings.AZURE_CLIENT_SECRET,
    #     'appName': "HR_module",
    # }
}
