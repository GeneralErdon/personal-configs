"""
                 ____       _   _   _                 
                / ___|  ___| |_| |_(_)_ __   __ _ ___ 
                \___ \ / _ \ __| __| | '_ \ / _` / __|
                 ___) |  __/ |_| |_| | | | | (_| \__ \
                |____/ \___|\__|\__|_|_| |_|\__, |___/
                                            |___/     

This file serves as the entry point for Django settings.

It imports all the modularized setting files, combining them into a single configuration:

- base: Core Django settings
- azure: Azure-specific settings for production
- cache: Caching configuration
- channels: Django Channels configuration
- debug_toolbar: Debug Toolbar settings
- drf: Django Rest Framework settings
- jwt: JSON Web Token authentication settings
- swagger: Swagger/OpenAPI documentation settings

This modular approach allows for better organization and easier management of different setting aspects.
"""

from .base import *
from .azure import *
from .cache import *
from .channels import *
from .debug_toolbar import *
from .django_unfold import *
from .drf import *
from .jwt import *
from .swagger import *