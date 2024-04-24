from apps.base.pagination import GenericOffsetPagination
from apps.base.viewsets.viewset_mixins import CreateObjectMixin, DestroyObjectMixin, ListObjectMixin, RetrieveObjectMixin, UpdateObjectMixin
from rest_framework import viewsets
from rest_framework.serializers import ModelSerializer


class GenericModelViewset(
            RetrieveObjectMixin,
            ListObjectMixin,
            CreateObjectMixin,
            UpdateObjectMixin,
            DestroyObjectMixin,
            viewsets.ModelViewSet
        ):
    
    serializer_class:ModelSerializer = None
    pagination_class = GenericOffsetPagination
    search_fields: list[str] = None


class GenericReadOnlyViewset(
            RetrieveObjectMixin,
            ListObjectMixin,
            viewsets.GenericViewSet,
        ):
    
    serializer_class:ModelSerializer = None
    pagination_class = GenericOffsetPagination
    search_fields: list[str] = None