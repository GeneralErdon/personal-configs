from rest_framework.pagination import LimitOffsetPagination

class GenericOffsetPagination(LimitOffsetPagination):
    default_limit = 100
    limit_query_param = "limit"
    offset_query_param = "offset"
    