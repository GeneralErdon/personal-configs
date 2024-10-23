from rest_framework.routers import DefaultRouter

class BaseRouter(DefaultRouter):
    """Añade el trailing slash para evitar los problemas que trae
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trailing_slash = '/?'