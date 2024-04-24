# from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from drf_yasg.generators import OpenAPISchemaGenerator
from rest_framework import permissions
from rest_framework.authentication import BasicAuthentication
from apps.users.views import Login, Logout
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

schema_view = get_schema_view(
    openapi.Info(
        title="Authentication API",
        default_version="v0.1.11032024",
        description="""
        Swagger documentation about the Auth API with JWT Token
        """,
        terms_of_service=None,
        contact=openapi.Contact(name="Leandro Fermín", email="leandrofermin@gmail.com"),
    ),
    public=True,
    generator_class=OpenAPISchemaGenerator,
    permission_classes=[permissions.IsAdminUser],
    authentication_classes=[BasicAuthentication]
)


urlpatterns = [
    # path('admin/', admin.site.urls),
    
    # Authentication
    re_path(r"^login/?$", Login.as_view(), name="login"),
    re_path(r"^logout/?$", Logout.as_view(), name="logout"),
    
    re_path(r'^refresh/?$', TokenRefreshView.as_view(), name='token_refresh'),
    re_path(r'^verify/?$', TokenVerifyView.as_view(), name='token_verify'),
    
    # Rutas
    path(r"users/", include('apps.users.api.routers'), name="users"),
    
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/?', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
] 



if settings.DEBUG:
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
