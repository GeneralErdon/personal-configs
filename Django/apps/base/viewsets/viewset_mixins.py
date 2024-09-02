from io import BytesIO
from typing import Any, Iterable
import datetime as dt
from django.db.models import QuerySet, Model
from django.http import QueryDict
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.http.response import Http404, HttpResponse
from django.core.exceptions import FieldError, ValidationError
from django.conf import settings
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.request import Request
from rest_framework.decorators import action
from rest_framework import status
from rest_framework_simplejwt.models import TokenUser
from apps.base.models import BaseModel
from apps.base.serializers import SQLSerializer

# Adding caching
from django.core.cache import cache

from apps.base.utils import RabbitMQManager



class ImplementReadOnlySerializer:
    """Esta clase es para implementar lo que es un serializador readOnly
    que estará optimizado para mostrar los datos.
    """
    read_only_serializer:ModelSerializer.__class__ = None

    def get_read_only_serializer(self, *args, **kwargs) -> ModelSerializer:
        assert self.read_only_serializer is not None, "Debe especificar la clase del readOnly Serializer"
        return self.read_only_serializer(*args, **kwargs)


class ImplementGenericResponses:

    @property
    def model_name(self):
        return self.serializer_class.Meta.model.__name__

    def get_not_found_response(self, message:str = None) -> Response:
        return Response({
            "message": message or "No se han encontrado resultados"
        }, status=status.HTTP_404_NOT_FOUND)

    def get_ok_response(self, data:dict[str, str], message:str = None) -> Response:
        if message is not None:
            data["message"] = message
        return Response(data, status=status.HTTP_200_OK)

    def get_created_response(self, data:dict[str, object] = None, message:str = None):
        data = data if data is not None else {}
        data["message"] = "Objeto {modelName} creado exitosamente".format(modelName=self.model_name)
        return Response(data, status=status.HTTP_201_CREATED)


    def get_bad_request(self, details:dict[str, object], message:str=None) -> Response:
        return Response({
            "message": message or "Ha ocurrido un error con su solicitud",
            **details,
        }, status=status.HTTP_400_BAD_REQUEST)


class GetQuerysetMixin:
    """Mixin para optimizar las consultas del ORM a la Database
    elimina los problemas del N + 1 utilizando el prefetch_related y el select_related
    """

    select_related_qs: list|tuple = tuple()
    prefetch_related_qs: list|tuple = tuple()
    qs_annotate: dict[str, object] = {}
    
    def get_related_queries(self) -> Iterable[str]:
        return self.select_related_qs

    def get_prefetch_queries(self) -> Iterable[str]:
        return self.prefetch_related_qs
    
    def get_annotate(self) -> dict[str, object]:
        return self.qs_annotate

    def get_queryset(self) -> QuerySet:
        model:Model = self.serializer_class.Meta.model
        qs = model.objects\
                .select_related(*self.get_related_queries())\
                .prefetch_related(*self.get_prefetch_queries())\
                .annotate(**self.get_annotate())
        
        return qs

class Implementations(
            ImplementReadOnlySerializer,
            ImplementGenericResponses,
            GetQuerysetMixin,
        ):
    
    def get_cache_key(self, request:Request):
        """Genera una llave para el cache que se pueda registrar en redis
        

        Args:
            request (Request): Request para generar el cache en base a eso

        Returns:
            str: Genera una llave con la sig nomenclatura: MODELNAME-/endpoint-query_params
        """
        model_name:str = self.serializer_class.Meta.model.__name__
        endpoint:str = request._request.path
        params = request.query_params.urlencode()
        cache_key:str = "{model}-{endpoint}-{params}"\
            .format(
                model=model_name.upper(),
                endpoint=endpoint,
                params=params
                )
        
        return cache_key
    
    def get_cache_data(self, cache_key:str) -> Any | None:
        """Método para la obtención de los datos del sistema de Cache.
        Si retorna None, entonces no encontró datos o el caché no está activo.

        Args:
            cache_key (str): Llave del contenido en el cache

        Returns:
            Any | None: Data si hay contenido, None si no encontró nada
        """
        if not settings.ACTIVE_CACHE: return None
        return cache.get(cache_key, None)
    
    def get_cache_pattern(self) -> str:
        """Función para obtener el patrón de cacheado del que 
        se van a extraer las llaves coincidentes

        Returns:
            str: El patrón
        """
        model_name:str = self.serializer_class.Meta.model.__name__
        # endpoint:str = request._request.path.replace("/", "")
        
        initial_key = f"{model_name.upper()}-*"
        return initial_key
    
    def clear_cache_pattern(self, patron:str):
        """Elimina las coincidencias de llaves de cache 
        en base al patrón.
        por ejemplo el patrón "user-*" va a eliminar
        todos las coincidencias que comiencen con user-

        Args:
            patron (str): El patrón del que se extraerán las llaves
        """
        cache_keys:list[str] = cache.keys(patron)
        cache.delete_many(cache_keys)
        
    
    def delete_queue_data(self, queue_name:str, id:int) -> None:
        
        rabbit_manager = RabbitMQManager()
        
        rabbit_manager.find_message_with_id(
            queue_name=queue_name,
            obj_id=id,
            auto_ack=True,
            )
    
    def publish_queue_data(self, queue_name:str, data:dict[str, Any]):
        rabbit_manager = RabbitMQManager()
        rabbit_manager.publish(queue_name,data)
        
        rabbit_manager.close()
    
    def get_request_data(self, request:Request) -> dict[str, Any]:
        """Metodo para obtener la data del request y colocarle el usuario que lo envió
        en el campo de "changed_by"

        Args:
            request (Request)

        Returns:
            dict[str, Any]: Returns with Changed_by user id.
        """
        user: TokenUser = request.user
        data = request.data.copy() # una copia del QueryDict o del Dict
        data["changed_by"] = user.id
        
        return data


class RetrieveObjectMixin(
            Implementations
        ):
    # Caching de low level agregado a la data serializada
    def retrieve(self, request, pk:str, *args, **kwargs):
        cache_key:str = self.get_cache_key(request=request)
        # Verifica primero si hay Cache
        serialized_cache_data = self.get_cache_data(cache_key)
        if serialized_cache_data:
            return self.get_ok_response(serialized_cache_data)
        

        obj:QuerySet|None = self.get_queryset().filter(pk=pk).first()

        if obj is not None:
            serializer = self.get_read_only_serializer(instance=obj)
            data = serializer.data
            
            if settings.ACTIVE_CACHE:
                cache.set(cache_key, data, settings.CACHE_LIFETIME)
                
            return self.get_ok_response(data)

        return self.get_not_found_response()

class ListObjectMixin(
            Implementations
        ):
    
    def process_value(self, value:str) -> str | bool | None:
        """Función para procesar los valores de un string
        la estoy aplicando a los obtenidos de los query params
        porque el query param envia todo como un string, acá los reemplazo por el tipo
        
        de esta forma se puede aplicar los filtros del django en la peticion.

        Args:
            value (str): Valor del query param

        Returns:
            Any: cualquier valor oyo
        """

        temp = value.lower()
        if temp == "true" or temp == "false":
            value = temp == "true"
        # elif temp.isnumeric():
        #     value = int(value)
        elif "," in temp:
            value = temp.split(",")
        elif temp == "null":
            value = None

        return value
    
    def get_filtros(self, query_params:QueryDict, excluded_keys:tuple[str]) -> tuple[dict, dict]:
        """Este método es para obtener los filtros para los métodos de "filter" y "exclude" 
        que irán en el querySet, provienen de la petición para así poder retornar 
        los filtros ya estructurados para ser aplicados en un queryset

        Args:
            query_params (QueryDict): QueryParams del request
            excluded_keys (tuple[str]): Llaves que serán excluidas del proceso como por ejemplo "page_size"

        Returns:
            tuple[dict, dict]: Tupla con los filtros que van en el metodo "filter" y los exclude que van en el método "exclude"
        """
        filtros, exclude = {}, {}

        for k, v in query_params.items():
            if k not in excluded_keys:
                v = self.process_value(v)
                filtros[k] = v

        if "exclude" in query_params:
            obs = query_params.getlist("exclude")
            for ob in obs:
                k, v, *_ = ob.split("=")
                exclude[k] = self.process_value(v)


        return filtros, exclude
    
    
    def get_filtered_qs(self, filtros:dict[str,str], excludes:dict[str, str]):
        """Aplica los filtros y exclusiones

        Args:
            filtros (dict[str,str]): Diccionario de filtros, las llaves deben ser siguiente los lookup y campos del modelo Django como "user__id" por ejemplo
            excludes (dict[str, str]): Diccionario de Exclusiones, igualmente con las llaves siguiendo los lookup de django.

        Returns:
            QuerySet: Retorna el Queryset con los filtros aplicados.
        """
        
        qs:QuerySet = self.get_queryset().filter(**filtros)
        
        if excludes:
            for key, value in excludes.items():
                qs = getattr(qs, "exclude")(**{key:value})
        
        return qs
    
    def get_data(self, request:Request) -> tuple[dict|list, int]:
        """Funcion para obtener los datos ya procesados para un reporte
        aplica de una vez los filtros, el paginado
        Args:
            request (Request): Peticion que debe ser GET y tener query_params

        Returns:
            tuple[QuerySet, list]: Todo el queryset, los datos paginados en lista
        """
        query_params = request.query_params
        excluded_params = (
            "limit", "offset", "ordering", "search", "exclude", "formato",
        )
        
        filtros, excludes = self.get_filtros(query_params, excluded_params)
        
        try:
            data:QuerySet = self.get_filtered_qs(filtros, excludes)
            data = self.filter_queryset(data)
            paged_data:QuerySet = self.paginate_queryset(data)
        
        except (FieldError, ValueError, ValidationError) as err:
            return {"message": err.args[0]}, status.HTTP_400_BAD_REQUEST
        except Http404:
            return self.get_not_found_response()
        except Exception as err:
            return {"message": "Error desconocido al obtener la data %s" % err.args.__str__()}, status.HTTP_400_BAD_REQUEST
        
        return paged_data, status.HTTP_200_OK
    
    
    
    #! @method_decorator(cache_page(settings.CACHE_LIFETIME) if settings.ACTIVE_CACHE else lambda x: x)
    def list(self, request:Request, *args, **kwargs):
        cache_key:str = self.get_cache_key(request=request)
        
        # Verifica primero si hay Cache
        serialized_cache_data = self.get_cache_data(cache_key)
        if serialized_cache_data:
            return self.get_ok_response(serialized_cache_data)

        
        data, status_code = self.get_data(request=request)
        if not status_code == status.HTTP_200_OK:
            return Response(data, status_code)
        
        if data:
            serializer = self.get_read_only_serializer(data, many=True)
            paginated_response:Response = self.get_paginated_response(serializer.data)
            
            if settings.ACTIVE_CACHE:
                # Se activa sólo si el settings tiene el ACTIVE_CACHE True
                
                response_data = paginated_response.data # Get the paginated response data dict
                cache.set(cache_key, response_data, settings.CACHE_LIFETIME)
            
            # cachear el contenido del serializador
            return paginated_response

        return self.get_not_found_response()

class CreateObjectMixin(
            Implementations
        ):
    
    
    
    def create(self, request:Request, *args, **kwargs):

        data = self.get_request_data(request)
        serializer:ModelSerializer = self.get_serializer(data=data)
        if serializer.is_valid():
            instance = serializer.save()
            obj = self.get_read_only_serializer(instance=instance).data
            # Clear the cache
            if settings.ACTIVE_CACHE:
                self.clear_cache_pattern(self.get_cache_pattern())
            return self.get_created_response(obj)

        return self.get_bad_request(serializer.errors)

class UpdateObjectMixin(
            Implementations
        ):
    def update(self, request:Request, pk:str,  *args, **kwargs):
        partial:bool = kwargs.get("partial", False)
        instance:Model = self.get_queryset().filter(pk=pk).first()

        new_data:dict[str, object] = self.get_request_data(request)

        serializer:ModelSerializer = self.get_serializer(instance=instance, data=new_data, partial=partial)
        if serializer.is_valid():
            instance = serializer.save()
            data = self.get_read_only_serializer(instance=instance).data
            # Clear the cache
            if settings.ACTIVE_CACHE:
                self.clear_cache_pattern(self.get_cache_pattern())
            return self.get_ok_response(data, f"{self.model_name} se ha actualizado exitosamente")

        return self.get_bad_request(serializer.errors)

class DestroyObjectMixin(
            Implementations
        ):
    """Mixin Class for the destroy of the instance
    You need to rewrite the methods "get_deleted_status" if you
    want to stablish what data type means that the object is deactivated
    (defaults to False)
    you need to rewrite "get_status_field" if you want to specify
    that field of theinstance represents its active or deactivated status
    (defaults to "is_active" field)
    """

    def get_deleted_status(self) -> bool | Any:
        """Returns the data type that means a object is destroyed or
        deactivated

        for example, if you have a instance with 3 types of status
        like the Vale instance (valid, processed, nulled)
        you must override this method to nulled (for example)

        Returns:
            boolean | Any: defaults to False
        """
        model:BaseModel = self.serializer_class.Meta.model
        return model.deactivated_status

    def get_status_field(self) -> str:
        """This method returns the field name that represents the
        status of the instance

        for example, the field "status" or the default "is_active" that is default for User model

        Returns:
            str: Defaults to "status"
        """
        return "status"

    def destroy(self, request:Request, pk:str, *args, **kwargs):
        excludes = {self.get_status_field():self.get_deleted_status()}

        # Excluyo si ya está desactivado
        obj:Model|None = self.get_queryset().filter(pk=pk).exclude(**excludes).first()
        if obj is not None:
            # set the attribute of the status to the deleted value
            setattr(obj, self.get_status_field(), self.get_deleted_status())
            obj.save()
            serialized_data = self.get_read_only_serializer(instance=obj).data
            # Clear the cache
            if settings.ACTIVE_CACHE:
                self.clear_cache_pattern(self.get_cache_pattern())
            return self.get_ok_response(
                    serialized_data,
                    f"El objeto {self.model_name} desactivado correctamente",
                )

        return self.get_not_found_response()
