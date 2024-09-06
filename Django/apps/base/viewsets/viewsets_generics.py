from apps.base.pagination import GenericOffsetPagination
from apps.base.viewsets.viewset_mixins import CreateObjectMixin, DestroyObjectMixin, GetQuerysetMixin, ListObjectMixin, RetrieveObjectMixin, UpdateObjectMixin
from rest_framework import viewsets
from rest_framework.serializers import ModelSerializer


class GenericModelViewset(
            GetQuerysetMixin,
            RetrieveObjectMixin,
            ListObjectMixin,
            CreateObjectMixin,
            UpdateObjectMixin,
            DestroyObjectMixin,
            viewsets.ModelViewSet
        ):
    """Class for viewsets for read only data
    inly List and Retrieve
    
    properties:
    - serializer_class: Serializer
    - read_only_serializer: Serializer
    - update_serializer: Serializer
    - sql_serializer
    - search_fields: list[str]
    - select_related_fields: list|tuple 
    - prefetch_related_fields: list|tuple 
    - annotate_fields: dict[str, object] 
    """
    
    serializer_class:ModelSerializer = None
    pagination_class = GenericOffsetPagination
    search_fields: list[str] = None
    
    


class GenericReadOnlyViewset(
            GetQuerysetMixin,
            RetrieveObjectMixin,
            ListObjectMixin,
            viewsets.GenericViewSet,
        ):
    """Class for viewsets for read only data
    inly List and Retrieve
    
    properties:
    - serializer_class: Serializer
    - read_only_serializer: Serializer
    - update_serializer: Serializer
    - sql_serializer
    - search_fields: list[str]
    - select_related_fields: list|tuple 
    - prefetch_related_fields: list|tuple 
    - annotate_fields: dict[str, object] 
    """
    
    
    serializer_class:ModelSerializer = None
    pagination_class = GenericOffsetPagination
    search_fields: list[str] = None
    
    