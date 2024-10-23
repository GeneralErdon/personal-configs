"""
                     _ __        _____ 
                    | |\ \      / /_  |
                 _  | |_\ \ /\ / /  | |
                | |_| |  \ V  V /   | |
                 \___/    \_/\_/    |_|
                                       
This file contains the configuration for JSON Web Tokens (JWT) authentication.

It defines settings for both development and production environments:

- ACCESS_TOKEN_LIFETIME: Duration for which access tokens are valid.
- REFRESH_TOKEN_LIFETIME: Duration for which refresh tokens are valid.
- UPDATE_LAST_LOGIN: Whether to update the last login timestamp on token refresh.
- SIGNING_KEY and ALGORITHM: Specifications for token signing.

Adjust these settings based on your security requirements and expected user session durations.
"""

from datetime import timedelta
from .base import env, DEBUG

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1200),  
    'REFRESH_TOKEN_LIFETIME': timedelta(hours=2400),

    # 'ROTATE_REFRESH_TOKENS': True,
    # 'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    # Default alghorithm and Signing Key specification
    'SIGNING_KEY': env.str("DJANGO_JWT_SIGNING_KEY"),
    "ALGORITHM": "HS256",
}

if not DEBUG:
    SIMPLE_JWT = {
        'ACCESS_TOKEN_LIFETIME': timedelta(hours=12),  
        'REFRESH_TOKEN_LIFETIME': timedelta(hours=24),

        # 'ROTATE_REFRESH_TOKENS': True,
        # 'BLACKLIST_AFTER_ROTATION': True,
        'UPDATE_LAST_LOGIN': True,
        # Default alghorithm and Signing Key specification
        'SIGNING_KEY': env.str("DJANGO_JWT_SIGNING_KEY"),
        "ALGORITHM": "HS256",
    }