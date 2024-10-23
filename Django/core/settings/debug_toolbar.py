"""
                 ____       _                   _____           _ _               
                |  _ \  ___| |__  _   _  __ _  |_   _|__   ___ | | |__   __ _ _ __
                | | | |/ _ \ '_ \| | | |/ _` |   | |/ _ \ / _ \| | '_ \ / _` | '__|
                | |_| |  __/ |_) | |_| | (_| |   | | (_) | (_) | | |_) | (_| | |   
                |____/ \___|_.__/ \__,_|\__, |   |_|\___/ \___/|_|_.__/ \__,_|_|   
                                        |___/                                      

This file contains the configuration for Django Debug Toolbar.

It defines the settings that control when and how the Debug Toolbar is displayed:

- The SHOW_TOOLBAR_CALLBACK setting determines when the toolbar should be shown.
- Currently, it's set to show only when DEBUG mode is active.

Adjust these settings as needed for your development environment.
"""

from django.conf import settings

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: settings.DEBUG,
}