from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from apps.base.viewsets.viewsets_generics import GenericModelViewset
from apps.base.viewsets.viewset_mixins import ReportViewMixin
from apps.users.api.serializers.user_serializers import UserReadOnlySerializer, UserSerializer
from apps.users.models import User, ADMINISTRATIVE_ROLE



class UserModelViewset(ReportViewMixin, GenericModelViewset):
    serializer_class = UserSerializer
    read_only_serializer = UserReadOnlySerializer
    search_fields = [
        "username",
        "first_name",
        "last_name",
    ]
    
    
    prefetch_related_qs = [
        "groups__content_type",
        "user_permissions__content_type",
    ]
    