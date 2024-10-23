# from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from apps.base.openapi import CustomSchemaGenerator
from rest_framework import permissions
from apps.users.views import Logout, AzureLogin
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from django.contrib import admin
from apps.base.oauth.authentication import AzureSwaggerAuthentication
from apps.users.views import AzureAdminLogin

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
    generator_class=CustomSchemaGenerator,
    permission_classes=[permissions.IsAdminUser],
    authentication_classes=[AzureSwaggerAuthentication]
)


urlpatterns = [
    re_path(r'^api/v1/admin/oauth2/callback/?$', AzureAdminLogin.as_view(), name='azure_admin_callback'),
    re_path(r'^api/v1/admin/?', admin.site.urls, name='admin'),
    
    # Authentication
    # re_path(r"^api/v1/login/?$", Login.as_view(), name="login"),
    
    re_path(r"^api/v1/oauth2/callback/?$", AzureLogin.as_view(), name="azure_login"),
    re_path(r"^api/v1/logout/?$", Logout.as_view(), name="logout"),
    
    re_path(r'^api/v1/refresh/?$', TokenRefreshView.as_view(), name='token_refresh'),
    re_path(r'^api/v1/verify/?$', TokenVerifyView.as_view(), name='token_verify'),
    
    # Rutas
    path(r"api/v1/users/", include('apps.users.api.router'), name="users"),
    path(r"api/v1/company/", include('apps.human_resources.company.api.router'), name="company"),
    path(r"api/v1/employees/", include('apps.human_resources.employees.api.router'), name="employees"),
    path(r"api/v1/payments/", include('apps.human_resources.payment.api.router'), name="payments"),
    path(r"api/v1/vacations/", include('apps.human_resources.vacation.api.router'), name="vacations"),
    path(r"api/v1/notifications/", include('apps.notifications.api.router'), name="notifications"),
    re_path(r'^api/v1/swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^api/v1/swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^api/v1/redoc/?', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
] 


if settings.DEBUG:
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
