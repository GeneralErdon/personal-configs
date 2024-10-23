"""
                  ____           _          
                 / ___|__ _  ___| |__   ___ 
                | |   / _` |/ __| '_ \ / _ \
                | |__| (_| | (__| | | |  __/
                 \____\__,_|\___|_| |_|\___|
                                            
This file contains the configuration for Django's caching system.

It defines the caching backend and related settings for both development and production environments:

- ACTIVE_CACHE: Determines whether caching is enabled.
- CACHE_BACKEND: Specifies the type of cache to use (FILES or REDIS).
- CACHES: Configures the caching backend based on the selected type.
- CACHE_LIFETIME: Sets the default cache lifetime, which differs between development and production.

For Redis:
- It includes configuration for both non-SSL (development) and SSL (production) connections.
- Redis-related environment variables are defined for host, port, password, and database.

Adjust these settings based on your application's caching needs and available infrastructure.
"""

from pathlib import Path
from .base import env, BASE_DIR, DEBUG


ACTIVE_CACHE = env.bool("DJANGO_ACTIVE_CACHE", True)
CACHE_BACKEND = env.str("DJANGO_CACHE_BACKEND", "FILES").upper()
REDIS_HOST = env.str('REDIS_HOST', "localhost")
REDIS_PORT = env.int('REDIS_PORT', 6380)
REDIS_PASSWORD = env.str('REDIS_PASSWORD', None)
REDIS_DB = env.int('REDIS_DB', 0)

if CACHE_BACKEND == "FILES" and ACTIVE_CACHE:
    CACHES = {
        "default": {
            "BACKEND":"django.core.cache.backends.filebased.FileBasedCache",
            "LOCATION": Path(BASE_DIR, "django_cache").resolve()
        }
    }
elif CACHE_BACKEND == "REDIS" and ACTIVE_CACHE:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                #"PASSWORD": REDIS_PASSWORD,
            }
        }
    }

CACHE_LIFETIME = 60 * 15 # in seconds

if not DEBUG:
    CACHE_LIFETIME = 60 * 60 * 24 * 30 # 1 month
    
    
    if CACHE_BACKEND == "REDIS" and ACTIVE_CACHE:
        CACHES = {
            "default": {
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": f"rediss://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}",
                "OPTIONS": {
                    "CLIENT_CLASS": "django_redis.client.DefaultClient",
                    "PASSWORD": REDIS_PASSWORD,
                    "SSL": True,
                }
            }
        }