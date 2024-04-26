from rest_framework.routers import DefaultRouter

class CustomRouter(DefaultRouter):
    """it permits the possibility of execute API regex with optional slash
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trailing_slash = '/?'