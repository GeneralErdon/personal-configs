from typing import Any
from django.conf import settings
from django.db.models import Model
from django.core.cache import cache
from rest_framework.request import Request
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

class CacheManager:
    
    @staticmethod
    def cache_page():
        return method_decorator(cache_page(settings.CACHE_LIFETIME) if settings.ACTIVE_CACHE else lambda x: x)
    
    def __init__(self, model:Model) -> None:
        self.__model:Model = model
    
    @property
    def model(self) -> Model:
        return self.__model
    
    @model.setter
    def model(self, value:Model):
        assert isinstance(value, Model), "Debe ser un modelo"
        self.__model = value
    
    @property
    def is_active(self) -> bool:
        """
        Verify if settings have Active c ache = True
        Returns: True if active False otherwise
        """
        return settings.ACTIVE_CACHE
    
    def get_model_name(self) -> str:
        """Función para obtener el nombre del modelo en MAYUSCULAS
        Returns:
            str
        """
        model_name:str = self.model.__name__.upper()
        return model_name
    
    def get_model_cache_pattern(self,) -> str:
        """Función para obtener el patrón de cacheado del que 
        se van a extraer las llaves coincidentes

        Returns:
            str: El patrón
        """
        model_name:str = self.get_model_name()
        initial_key = f"{model_name}-*"
        return initial_key
    
    def get_cache_key(self, request:Request) -> str:
        """This method is for generate the cache key depending of the requirements
        this method must be overrided in every new inheritance

        Args:
            request (Request): The rest will be provided for generate the cache key
        Raises:
            NotImplementedError: In case the method is not overrided
        Returns:
            str: The formated cache Key
        """
        raise NotImplementedError(f"Se debe especificar el algoritmo de cache Key")
    
    def get_cache_data(self,*, request:Request = None, cache_key:str = None) -> Any | None:
        """Método para la obtención de los datos del sistema de Cache.
        Si retorna None, entonces no encontró datos o el caché no está activo.

        Args:
            cache_key (str): Llave del contenido en el cache

        Returns:
            Any | None: Data si hay contenido, None si no encontró nada
        """
        if not self.is_active: return
        assert (request is None) != (cache_key is None), "Debe proveer o el request o el cache_key"
        
        # Si provee el request setea cache_key desde el metodo, si no hay request, usa el cache_key del parametro
        if request:
            cache_key:str = self.get_cache_key(request)
        
        return cache.get(cache_key, None)
    
    def set_cache_data(self, cache_key:str, data:Any, lifetime:int = None) -> None:
        """Sets the cache data using the cache key and lifetime if provided

        Args:
            cache_key (str): Cache key where the data will be set
            data (Any): Data to be setted
            lifetime (int, optional): Timeout or lifetime of cache data, if not provided will use default cache lifetime. Defaults to None.
        """
        if not self.is_active: return
        cache.set(cache_key, data, lifetime)
    
    def clear_all_cache(self):
        """
        Deletes ALL cache, don't use it until it's necessary
        """
        cache.clear()
    
    def clear_cache_pattern(self, pattern:str):
        """Elimina las coincidencias de llaves de cache 
        en base al patrón.
        por ejemplo el patrón "user-*" va a eliminar
        todos las coincidencias que comiencen con user-

        Args:
            patron (str): El patrón del que se extraerán las llaves
        """
        if not self.is_active: return
        cache_keys:list[str] = cache.keys(pattern)
        cache.delete_many(cache_keys)


