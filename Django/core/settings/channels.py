"""
                  ____ _                            _     
                 / ___| |__   __ _ _ __  _ __   ___| |___ 
                | |   | '_ \ / _` | '_ \| '_ \ / _ \ / __|
                | |___| | | | (_| | | | | | | |  __/ \__ \
                 \____|_| |_|\__,_|_| |_|_| |_|\___|_|___/
                                                          
This file contains the configuration for Django Channels.

It sets up the Channel Layers for both development and production environments:

- In development, it uses a simple Redis configuration.
- In production, it uses a secure Redis configuration with SSL.

The file also defines Redis-related environment variables used in the configurations.

Remember to adjust these settings according to your specific Redis setup and security requirements.
"""

from .base import env, DEBUG
REDIS_HOST = env.str("REDIS_HOST", "localhost")
REDIS_PORT = env.int("REDIS_PORT", 6380)
REDIS_PASSWORD = env.str("REDIS_PASSWORD", None)
REDIS_DB = env.int("REDIS_DB", 0)

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(env.str("REDIS_HOST"), env.int("REDIS_PORT"))],
        },
    }
}

if not DEBUG:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [f"rediss://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"],
                "ssl_cert_reqs": None,
            },
        }
    }