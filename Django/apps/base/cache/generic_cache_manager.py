
from apps.base.cache.base_manager import CacheManager
from rest_framework.request import Request

class ViewsetCacheManager(CacheManager):
    def get_cache_key(self, request: Request) -> str:
        """
        This method is for generate a Cache key with this structure:
        
        Example: "model_name-endpoint-query_params"
        
        Returns:
            str: Cache key
        
        """
        model_name = self.get_model_name()
        endpoint = request._request.path
        query_params:str = request.query_params.urlencode()
        return f"{model_name}-{endpoint}:{request.user.pk}:{query_params}"
