from io import BytesIO
from typing import Any
import datetime as dt
from django.db.models import QuerySet, Model
from django.http import QueryDict
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.http.response import Http404, HttpResponse
from django.core.exceptions import FieldError, ValidationError
from django.conf import settings
import pandas as pd
from xlsxwriter.workbook import Workbook
from xlsxwriter.worksheet import Worksheet
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.request import Request
from rest_framework.decorators import action
from rest_framework import status
from rest_framework_simplejwt.models import TokenUser
from apps.base.models import BaseModel
from apps.base.serializers import SQLSerializer
from apps.base.cache.generic_cache_manager import ViewsetCacheManager

# Adding caching


# ===== Base Mixins
class BaseMixin:
    serializer_class:ModelSerializer = None
    read_only_serializer:ModelSerializer.__class__ = None
    update_serializer:ModelSerializer.__class__ = None
    
    @property
    def model_name(self) -> str:
        """
        Returns the model name as string
        """
        return self.serializer_class.Meta.model.__name__
    
    
    def get_update_serializer(self, *args, **kwargs) -> ModelSerializer:
        """
        Devuelve un serializador para los Update y Patch de forma opcional
        
        Retorna la instancia del serializador, por lo que se debe pasar por parametros
        los mismos que un model serializer
        """
        
        return self.update_serializer(*args, **kwargs) if self.update_serializer else self.serializer_class(*args, **kwargs)
    
    def get_readonly_serializer(self, *args, **kwargs) -> ModelSerializer:
        """
        Obliga la especificacion de un Serializador Read Only.
        para la visibilización de los datos
        
        Retorna la instancia del serializador, por lo que se debe pasar por parametros
        los mismos que un model serializer
        """
        assert self.read_only_serializer is not None, "Debe especificar la clase del readOnly Serializer"
        return self.read_only_serializer(*args, **kwargs)
    
    def get_model(self) -> Model.__class__:
        """
        Returns the model class from the serializer_class
        """
        return self.serializer_class.Meta.model

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
    # =====================================================================
    #                           Generic Responses
    # =====================================================================
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



class GetQuerysetMixin(BaseMixin):
    """Mixin para optimizar las consultas del ORM a la Database
    elimina los problemas del N + 1 utilizando el prefetch_related y el select_related
    """

    select_related_fields: list|tuple = tuple()
    prefetch_related_fields: list|tuple = tuple()
    annotate_fields: dict[str, object] = {}

    def get_related_fields(self) -> list[str] | tuple[str]:
        return self.select_related_fields
    
    def get_prefetch_fields(self) -> list[str] | tuple[str]:
        return self.prefetch_related_fields

    def get_annotate(self) -> dict[str, object]:
        return self.annotate_fields

    def get_queryset(self) -> QuerySet:
        """Function returns optimized Queryset using the select_related
        and prefetch specified in the class
        Rememeber specify the select_related_fields and prefetch_related_fields properties for optimization
        
        annotate_fields is optional for annotate functionality

        Returns:
            QuerySet: Queryset optimized
        """
        qs = self.get_model().objects\
                .select_related(*self.get_related_fields())\
                .prefetch_related(*self.get_prefetch_fields())\
                .annotate(**self.get_annotate())
        return qs


class RetrieveObjectMixin(BaseMixin):
    
    def retrieve(self, request, pk:str, *args, **kwargs):
        # Verifica primero por cache
        cache_manager = ViewsetCacheManager(self.get_model())
        cache_key:str = cache_manager.get_cache_key(request=request)
        serialized_cache_data = cache_manager.get_cache_data(cache_key=cache_key)
        if serialized_cache_data:
            return self.get_ok_response(serialized_cache_data)
        
        # No encontró nada en cache o no estaba activo
        obj:QuerySet|None = self.get_queryset().filter(pk=pk).first()

        if obj is not None:
            serializer = self.get_readonly_serializer(instance=obj)
            data = serializer.data
            
            cache_manager.set_cache_data(cache_key, data, settings.CACHE_LIFETIME)
            
            return self.get_ok_response(data)

        return self.get_not_found_response()

class ListObjectMixin(BaseMixin):
    special_query_params = (
            "limit", "offset", "ordering", "search", "exclude", "formato", "page", "page_size"
        )
    
    def get_special_query_params(self) -> list[str] | tuple[str]:
        """
        This functions extract a property with query params that will not be
        used as a filter param, just for special purposes like pagination, etc
        """
        return self.special_query_params
    
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
        excluded_params = self.get_special_query_params()
        
        filtros, excludes = self.get_filtros(query_params, excluded_params)
        
        try:
            data:QuerySet = self.get_filtered_qs(filtros, excludes)
            data = self.filter_queryset(data)
            paged_data:QuerySet = self.paginate_queryset(data)
        
        except (FieldError, ValueError, ValidationError) as err:
            return {"message": err.args[0]}, status.HTTP_400_BAD_REQUEST
        except Http404:
            return {"message": "No se han encontrado resultados"}, status.HTTP_404_NOT_FOUND
        except Exception as err:
            return {"message": "Error desconocido al obtener la data %s" % err.args.__str__()}, status.HTTP_400_BAD_REQUEST
        
        return paged_data, status.HTTP_200_OK
    
    def list(self, request: Request, *args, **kwargs):
        # Instancia el gestor de cache
        cache_manager = ViewsetCacheManager(self.get_model())
        cache_key: str = cache_manager.get_cache_key(request=request)
        
        # Verifica primero si hay Cache
        serialized_cache_data = cache_manager.get_cache_data(cache_key=cache_key)
        if serialized_cache_data:
            return self.get_ok_response(serialized_cache_data)

        # Obtiene los datos
        data, status_code = self.get_data(request=request)
        if not status_code == status.HTTP_200_OK:
            return Response(data, status_code)

        if data:
            # Serializa los datos
            serializer = self.get_readonly_serializer(data, many=True)
            paginated_response: Response = self.get_paginated_response(serializer.data)
            response_data = paginated_response.data  # Obtener el dict de la respuesta paginada
            cache_manager.set_cache_data(cache_key, response_data, settings.CACHE_LIFETIME)
            
            # Devuelve la respuesta paginada
            return paginated_response

        return self.get_not_found_response()


class CreateObjectMixin(BaseMixin):
    
    def create(self, request:Request, *args, **kwargs):
        cache_manager = ViewsetCacheManager(self.get_model())
        data = self.get_request_data(request)
        serializer:ModelSerializer = self.get_serializer(data=data)
        if serializer.is_valid():
            instance = serializer.save()
            obj = self.get_readonly_serializer(instance=instance).data
            
            # Clear the cache for this Model
            cache_manager.clear_cache_pattern(cache_manager.get_model_cache_pattern())
            
            return self.get_created_response(obj)

        return self.get_bad_request(serializer.errors)

class UpdateObjectMixin(BaseMixin):
    def update(self, request:Request, pk:str,  *args, **kwargs):
        cache_manager = ViewsetCacheManager(self.get_model())
        partial:bool = kwargs.get("partial", False)
        instance:Model = self.get_queryset().filter(pk=pk).first()

        new_data:dict[str, object] = self.get_request_data(request)

        serializer:ModelSerializer = self.get_update_serializer(instance=instance, data=new_data, partial=partial)
        if serializer.is_valid():
            instance = serializer.save()
            data = self.get_readonly_serializer(instance=instance).data
            
            # Clear the cache for this Model
            cache_manager.clear_cache_pattern(cache_manager.get_model_cache_pattern())
            
            return self.get_ok_response(data, f"{self.model_name} se ha actualizado exitosamente")

        return self.get_bad_request(serializer.errors)

class DestroyObjectMixin(BaseMixin):
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
        cache_manager = ViewsetCacheManager(self.get_model())
        excludes = {self.get_status_field():self.get_deleted_status()}

        # Excluyo si ya está desactivado
        obj:Model|None = self.get_queryset().filter(pk=pk).exclude(**excludes).first()
        if obj is not None:
            # set the attribute of the status to the deleted value
            setattr(obj, self.get_status_field(), self.get_deleted_status())
            obj.save()
            serialized_data = self.get_readonly_serializer(instance=obj).data
            # Clear the cache for this Model
            cache_manager.clear_cache_pattern(cache_manager.get_model_cache_pattern())
            return self.get_ok_response(
                    serialized_data,
                    f"El objeto {self.model_name} desactivado correctamente",
                )

        return self.get_not_found_response()


class ReportViewMixin:
    """View mixin for generate reports in excel or CSV
    
    - read_only_serializer
    - sql_serializer: SQLSerializer
    

    Returns:
        _type_: _description_
    """
    read_only_serializer = None
    sql_serializer:SQLSerializer = None
    # use_get_annotate = False #?Para utilizar el self.get_annotate en el reports

    def get_filename(self) -> str:
        model_name:str = self.serializer_class.Meta.model.__name__
        fecha = dt.date.today().strftime("%d-%m-%Y")


        return "%s-%s" % (model_name, fecha)

    def get_sql_serializer(self, *args, **kwargs) -> SQLSerializer:
        assert self.sql_serializer is not None, (
            'la clase %s debería de contar con un '
            'serializador sql para la funcion de exportar'
            'a excel o csv.' % self.basename
        )

        return self.sql_serializer(*args, **kwargs)

    def estilizar_excel(self, workbook:Workbook, worksheet:Worksheet, df:pd.DataFrame):

        header_format = workbook.add_format({
            "bg_color": "#FF5400",
            "bold": True,
            "border": 1,
            })



        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format )

        worksheet.autofilter(0, 0, 0, len(df.columns)-1)

        max_row, max_col = df.shape

        # worksheet.conditional_format("A2:A7", options={
        #     "type":"3_color_scale",
        #     "min_color": "#1ED760",
        #     "mid_color": "#0088D2",
        #     "max_color": "#A95EFF"
        #     })
        #worksheet.conditional_format("A2:E7", {"format":header_format})


    def generate_excel_file(self, data:QuerySet) -> tuple[bytes, str]:
        """Función que debe recibir un queryset para generar un excel
        utilizando pandas, con xlswriter,
        utiliza también un serializador para el Queryset, que
        los convierten en listas de diccionarios. para poder
        transformarlos a dataFrame de pandas.

        https://xlsxwriter.readthedocs.io/working_with_pandas.html

        Args:
            data (QuerySet): Queryset de algun lado XD

        Returns:
            tuple[bytes, str]: Retorna los Binarios del archivo excel (para no guardarlo),
                    y el nombre del archivo
        """
        serializer = self.get_sql_serializer(instance=data, many=True)
        serialized_data = serializer.data

        df = pd.DataFrame(serialized_data)
        filename = self.get_filename()

        output_bytes = BytesIO()

        #df["created_date"] = df["created_date"].dt.tz_localize(None)

        excel_writer = pd.ExcelWriter(
            output_bytes, engine="xlsxwriter",
            date_format="d/mmm/yyyy", datetime_format="d/mmm/yyyy  hh:mm:ss",
            )


        # Escribe el archivo por chunks para ahorrar memoria
        for _, chunk in enumerate(df.groupby(df.index // 10_000)):

            chunk[1].to_excel(excel_writer=excel_writer, index=False, sheet_name=filename, )


        # Estilizado del Excel
        workbook:Workbook = excel_writer.book
        worksheet:Worksheet = excel_writer.sheets[filename]
        self.estilizar_excel(workbook, worksheet, df)


        # Estilizar el HEADER de las columnas


        # Cierra el archivo
        excel_writer.close()

        excel_data = output_bytes.getvalue()

        return excel_data, filename

    def generate_csv_file(self, data) -> tuple[bytes, str]:
        serializer = self.get_sql_serializer()
        serialized_data = serializer(data)
        df = pd.DataFrame(serialized_data)
        filename = self.get_filename()

        output_bytes = BytesIO()

        df.to_csv(output_bytes, ';',)

        return output_bytes.getvalue(), filename




    # Al reporte de excel si le agrego cache por vista debido a que así 
    # cacheo la parte de generacion de Excel con Pandas.
    @method_decorator(cache_page(settings.CACHE_LIFETIME) if settings.ACTIVE_CACHE else lambda x: x)
    @action(methods=["GET"], detail=False)
    def download_report(self, request:Request, *args, **kwargs):
        data, status_code = self.get_data(request=request)

        if status_code != status.HTTP_200_OK:
            return Response(data, status_code)

        formats = {
            "csv": (self.generate_csv_file, "csv"),
            "excel": (self.generate_excel_file, "xlsx"),
            #"grafico": ...,
        }

        if "formato" in request.query_params:
            tipo_formato:str = request.query_params["formato"].lower()
            
            parser_func = formats.get(tipo_formato, None)
            
            if parser_func is None:
                return Response(
                    {"message": "Formato no disponible, sólo csv, excel"},
                    status.HTTP_400_BAD_REQUEST
                    )
            
            parser_func, file_extension = parser_func

            file_data, filename = parser_func(data)

            return HttpResponse(
                    file_data, 
                    content_type="text/%s" % file_extension,
                    headers= {
                        "Content-Disposition": 'attachment; filename="%s.%s"'
                        %
                        (filename, file_extension) }
                )


        excel_response, filename = self.generate_excel_file(data)

        return HttpResponse(
                excel_response, content_type="text/xlsx",
                headers= {"Content-Disposition": 'attachment; filename="%s.xlsx"' % filename }
            )

