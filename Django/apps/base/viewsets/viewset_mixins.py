from io import BytesIO
from typing import Any, Callable
import datetime as dt
from django.db.models import QuerySet, Model
from django.http import QueryDict
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.http.response import Http404, HttpResponse
from django.core.exceptions import FieldError, ValidationError
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
import pandas as pd
from xlsxwriter.workbook import Workbook
from xlsxwriter.worksheet import Worksheet
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.request import Request
from rest_framework.decorators import action
from rest_framework import status
from apps.base.models import BaseModel
from apps.base.serializers import BaseReadOnlySerializer, SQLSerializer
from apps.base.cache.generic_cache_manager import ViewsetCacheManager
from django.utils.translation import gettext_lazy as _
from apps.base.responses import BaseResponse
from django.utils import timezone
# Adding caching


# ===== Base Mixins
class BaseMixin:
    serializer_class:ModelSerializer.__class__ = None
    read_only_serializer:ModelSerializer.__class__ = None
    update_serializer:ModelSerializer.__class__ = None
    
    @property
    def model_name(self) -> str:
        """
        Returns the model name as a string.

        Returns:
            str: The name of the model associated with the serializer class.
        """
        return self.serializer_class.Meta.model.__name__
    
    
    def _get_serializer(self, serializer_class:ModelSerializer.__class__, *args, **kwargs) -> ModelSerializer:
        """
        Returns an instance of the specified serializer class.

        Args:
            serializer_class (ModelSerializer.__class__): The serializer class to instantiate.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            ModelSerializer: An instance of the specified serializer class.
        """
        kwargs.setdefault('context', self.get_serializer_context())
        serializer = serializer_class(*args, **kwargs)
        return serializer
    
    def get_update_serializer(self, *args, **kwargs) -> ModelSerializer:
        """
        Returns an instance of the update serializer class.
        If no update_serializer is specified, it falls back to the default serializer_class.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            ModelSerializer: An instance of the update serializer or default serializer class.
        """
        serializer = self._get_serializer(self.update_serializer, *args, **kwargs) if self.update_serializer else self._get_serializer(self.serializer_class, *args, **kwargs)
        return serializer
    
    def get_readonly_serializer(self, *args, **kwargs) -> ModelSerializer:
        """
        Forces the specification of a Read Only Serializer for the visibility of the data.
        
        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            ModelSerializer: An instance of the readOnly serializer.

        Raises:
            AssertionError: If read_only_serializer is not specified.
        """
        assert self.read_only_serializer is not None, "Must specify the readOnly Serializer class"
        serializer = self._get_serializer(self.read_only_serializer, *args, **kwargs)
        return serializer
    
    def get_model(self) -> Model.__class__:
        """
        Returns the model class associated with the serializer_class.

        Returns:
            Model.__class__: The model class from the serializer_class.
        """
        return self.serializer_class.Meta.model

    # =====================================================================
    #                           Generic Responses
    # =====================================================================
    def get_not_found_response(self, message:str = None) -> Response:
        """
        Returns a not found response.

        Args:
            message (str, optional): Custom message for the response. Defaults to None.

        Returns:
            Response: A not found response.
        """
        return BaseResponse.not_found(message=message)

    def get_ok_response(self, data:dict[str, str], message:str = None) -> Response:
        """
        Returns an OK response with the provided data.

        Args:
            data (dict[str, str]): The data to be included in the response.
            message (str, optional): Custom message for the response. Defaults to None.

        Returns:
            Response: An OK response with the provided data.
        """
        return BaseResponse.ok(data, message=message)

    def get_created_response(self, data:dict[str, object] = None, message:str = None):
        """
        Returns a created response with the provided data.

        Args:
            data (dict[str, object], optional): The data to be included in the response. Defaults to None.
            message (str, optional): Custom message for the response. Defaults to None.

        Returns:
            Response: A created response with the provided data.
        """
        data = data if data is not None else {}
        message = message or _("Object %s created successfully" % self.model_name)
        return BaseResponse.created(data, message=message)


    def get_bad_request(self, details:dict[str, object], message:str=None) -> Response:
        """
        Returns a bad request response with the provided details.

        Args:
            details (dict[str, object]): The details of the bad request.
            message (str, optional): Custom message for the response. Defaults to None.

        Returns:
            Response: A bad request response with the provided details.
        """
        return BaseResponse.bad_request(details, message=message)



class GetQuerysetMixin(BaseMixin):
    """
    Mixin to optimize ORM queries to the Database.
    Eliminates N+1 problems using prefetch_related and select_related.
    """

    select_related_fields: list|tuple = tuple()
    prefetch_related_fields: list|tuple = tuple()
    annotate_fields: dict[str, object] = {}

    def get_related_fields(self) -> list[str] | tuple[str]:
        """
        Returns the fields to be used with select_related.

        Returns:
            list[str] | tuple[str]: Fields for select_related.
        """
        return self.select_related_fields
    
    def get_prefetch_fields(self) -> list[str] | tuple[str]:
        """
        Returns the fields to be used with prefetch_related.

        Returns:
            list[str] | tuple[str]: Fields for prefetch_related.
        """
        return self.prefetch_related_fields

    def get_annotate(self) -> dict[str, object]:
        """
        Returns the fields to be used with annotate.

        Returns:
            dict[str, object]: Fields for annotate.
        """
        return self.annotate_fields

    def get_queryset(self) -> QuerySet:
        """
        Returns an optimized QuerySet using select_related and prefetch_related specified in the class.
        Remember to specify the select_related_fields and prefetch_related_fields properties for optimization.
        
        annotate_fields is optional for annotate functionality.

        Returns:
            QuerySet: Optimized QuerySet.
        """
        qs = self.get_model().objects\
                .select_related(*self.get_related_fields())\
                .prefetch_related(*self.get_prefetch_fields())\
                .annotate(**self.get_annotate())
        return qs


class RetrieveObjectMixin(BaseMixin):
    
    def retrieve(self, request, pk:str, *args, **kwargs):
        """
        Retrieves a single object by its primary key.
        Checks the cache first, if not found, queries the database.

        Args:
            request (Request): The request object.
            pk (str): The primary key of the object to retrieve.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: The retrieved object data or an error response.
        """
        # First, check the cache
        if not pk.isdigit():
            return self.get_bad_request({"pk": [_("Id expected, but got %s" % pk)]}, message=_("Invalid Pk received at the endpoint"))
        
        cache_manager = ViewsetCacheManager(self.get_model())
        cache_key:str = cache_manager.get_cache_key(request=request)
        serialized_cache_data = cache_manager.get_cache_data(cache_key=cache_key)
        if serialized_cache_data:
            return self.get_ok_response(serialized_cache_data)
        
        # If not found in cache or cache is not active
        obj:QuerySet|None = self.get_queryset().filter(pk=pk).first()

        if obj is not None:
            serializer = self.get_readonly_serializer(instance=obj)
            data = serializer.data
            
            cache_manager.set_cache_data(cache_key, data, settings.CACHE_LIFETIME)
            
            return self.get_ok_response(data)

        return self.get_not_found_response()

class ListObjectMixin(BaseMixin):
    special_query_params = (
            "limit", "offset", "ordering", "search", "exclude", "file_format", "page", "page_size"
        )
    
    def get_special_query_params(self) -> list[str] | tuple[str]:
        """
        Extracts a property with query params that will not be
        used as filter params, just for special purposes like pagination, etc.

        Returns:
            list[str] | tuple[str]: List of special query parameters.
        """
        return self.special_query_params
    
    def process_value(self, value:str) -> str | bool | None:
        """
        Processes the values from a string.
        Applied to values obtained from query params because the query param sends everything as a string.
        Here they are replaced by the appropriate type so that Django filters can be applied in the request.

        Args:
            value (str): Value of the query param.

        Returns:
            str | bool | None: Processed value.
        """

        temp = value.lower()
        if temp == "true" or temp == "false":
            value = temp == "true"
        elif "," in temp:
            value = temp.split(",")
        elif temp in ("null", "none", "undefined"):
            value = None
        

        return value
    
    def get_filtros(self, query_params:QueryDict, excluded_keys:tuple[str]) -> tuple[dict, dict]:
        """
        Obtains the filters for the "filter" and "exclude" methods that will go in the querySet.
        They come from the request to return the filters already structured to be applied in a queryset.

        Args:
            query_params (QueryDict): QueryParams of the request.
            excluded_keys (tuple[str]): Keys that will be excluded from the process, such as "page_size".

        Returns:
            tuple[dict, dict]: Tuple with the filters that go in the "filter" method and the excludes that go in the "exclude" method.
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
        """
        Applies the filters and exclusions to the queryset.

        Args:
            filtros (dict[str,str]): Dictionary of filters, the keys must follow the lookups and fields of the Django model, such as "user__id".
            excludes (dict[str, str]): Dictionary of Exclusions, also with keys following Django lookups.

        Returns:
            QuerySet: Returns the QuerySet with the applied filters.
        """
        
        qs:QuerySet = self.get_queryset().filter(**filtros)
        
        if excludes:
            for key, value in excludes.items():
                qs = getattr(qs, "exclude")(**{key:value})
        
        return qs
    
    def get_data(self, request:Request) -> tuple[dict|list, int]:
        """
        Function to obtain the already processed data for a report.
        Applies filters and pagination at once.

        Args:
            request (Request): Request that must be GET and have query_params.

        Returns:
            tuple[dict|list, int]: The processed data and the status code.
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
            return {"message": "No results found"}, status.HTTP_404_NOT_FOUND
        except Exception as err:
            return {"message": "Unknown error at get_data: %s" % err.args.__str__()}, status.HTTP_400_BAD_REQUEST
        
        return paged_data, status.HTTP_200_OK
    
    def list(self, request: Request, *args, **kwargs):
        """
        Lists objects based on the request parameters.
        Checks the cache first, if not found, queries the database.

        Args:
            request (Request): The request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: The list of objects or an error response.
        """
        # Instantiate the cache manager
        cache_manager = ViewsetCacheManager(self.get_model())
        cache_key: str = cache_manager.get_cache_key(request=request)
        
        # First check if there's Cache
        serialized_cache_data = cache_manager.get_cache_data(cache_key=cache_key)
        if serialized_cache_data:
            return self.get_ok_response(serialized_cache_data)

        # Get the data
        data, status_code = self.get_data(request=request)
        if not status_code == status.HTTP_200_OK:
            return Response(data, status_code)

        if data:
            # Serialize the data
            serializer = self.get_readonly_serializer(data, many=True)
            paginated_response: Response = self.get_paginated_response(serializer.data)
            response_data = paginated_response.data  # Get the dict of the paginated response
            cache_manager.set_cache_data(cache_key, response_data, settings.CACHE_LIFETIME)
            
            # Return the paginated response
            return paginated_response

        return self.get_not_found_response()


class CreateObjectMixin(BaseMixin):
    
    def create(self, request:Request, *args, **kwargs):
        """
        Creates a new object based on the request data.

        Args:
            request (Request): The request object containing the data for the new object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: The created object data or an error response.
        """
        cache_manager = ViewsetCacheManager(self.get_model())
        data = request.data
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
        """
        Updates an existing object based on the request data.

        Args:
            request (Request): The request object containing the data for updating the object.
            pk (str): The primary key of the object to update.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: The updated object data or an error response.
        """
        cache_manager = ViewsetCacheManager(self.get_model())
        partial:bool = kwargs.get("partial", False)
        instance:Model = self.get_queryset().filter(pk=pk).first()

        new_data:dict[str, object] = request.data

        serializer:ModelSerializer = self.get_update_serializer(instance=instance, data=new_data, partial=partial)
        if serializer.is_valid():
            instance = serializer.save()
            data = self.get_readonly_serializer(instance=instance).data
            
            # Clear the cache for this Model
            cache_manager.clear_cache_pattern(cache_manager.get_model_cache_pattern())
            
            return self.get_ok_response(data, f"{self.model_name} has been successfully updated")

        return self.get_bad_request(serializer.errors)

class DestroyObjectMixin(BaseMixin):
    """
    Mixin Class for the destruction of the instance.
    You need to override the methods "get_deleted_status" if you
    want to establish what data type means that the object is deactivated
    (defaults to False).
    You need to override "get_status_field" if you want to specify
    which field of the instance represents its active or deactivated status
    (defaults to "is_active" field).
    """

    def get_deleted_status(self) -> bool | Any:
        """
        Returns the data type that means an object is destroyed or deactivated.

        For example, if you have an instance with 3 types of status
        like the Vale instance (valid, processed, nulled),
        you must override this method to return 'nulled' (for example).

        Returns:
            boolean | Any: Defaults to False.
        """
        model:BaseModel = self.serializer_class.Meta.model
        return model.deactivated_status

    def get_status_field(self) -> str:
        """
        This method returns the field name that represents the status of the instance.

        For example, the field "status" or the default "is_active" that is default for User model.

        Returns:
            str: Defaults to "status".
        """
        return "status"

    def destroy(self, request:Request, pk:str, *args, **kwargs):
        """
        Deactivates (soft deletes) an object based on its primary key.

        Args:
            request (Request): The request object.
            pk (str): The primary key of the object to deactivate.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: The deactivated object data or a not found response.
        """
        cache_manager = ViewsetCacheManager(self.get_model())
        excludes = {self.get_status_field():self.get_deleted_status()}

        # Exclude if already deactivated
        obj:Model|None = self.get_queryset().filter(pk=pk).exclude(**excludes).first()
        if obj is not None:
            # Set the attribute of the status to the deleted value
            setattr(obj, self.get_status_field(), self.get_deleted_status())
            obj.save()
            serialized_data = self.get_readonly_serializer(instance=obj).data
            # Clear the cache for this Model
            cache_manager.clear_cache_pattern(cache_manager.get_model_cache_pattern())
            return self.get_ok_response(
                    serialized_data,
                    f"The object {self.model_name} has been successfully deactivated",
                )

        return self.get_not_found_response()


class ReportViewMixin(BaseMixin):
    """
    View mixin for generating reports in Excel or CSV format.
    
    Attributes:
        export_csv_serializer (SQLSerializer | BaseReadOnlySerializer | None): Serializer used for exporting data.
    """
    export_csv_serializer:SQLSerializer | BaseReadOnlySerializer | None = None

    def get_filename(self) -> str:
        """
        Returns the filename for the report.

        Returns:
            str: The filename, consisting of the model name and current date.
        """
        
        model_name:str = self.get_model().__name__
        fecha = timezone.now().strftime("%d-%m-%Y")


        return "%s-%s" % (model_name, fecha)

    def get_export_serializer(self, *args, **kwargs) -> SQLSerializer | BaseReadOnlySerializer:
        """
        Returns the serializer instance for exporting data.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            SQLSerializer | BaseReadOnlySerializer: The serializer instance.

        Raises:
            AssertionError: If export_csv_serializer is not defined.
        """
        assert self.export_csv_serializer is not None, (
            'the class %s should have a sql serializer '
            'to export to excel or csv.' % self.basename
        )
        serializer = self._get_serializer(self.export_csv_serializer, *args, **kwargs)

        return serializer

    def get_excel_header_format(self) -> dict:
        """
        Returns the format for the header of the Excel file.

        Returns:
            dict: The format for the header.
        """
        return {
            "bg_color": "#8CE09B",
            "bold": True,
            "border": 1,
        }
    def set_excel_column_styles(self, workbook:Workbook, worksheet:Worksheet, col_num:int, value:str, header_format:dict):
        """
        Sets custom styles for the column in the Excel file.

        Args:
            workbook (Workbook): The Excel workbook.
            worksheet (Worksheet): The worksheet being styled.
            col_num (int): The column number.
            value (str): The column header value.
            header_format (dict): The header format dictionary.
        """
        pass

    def set_excel_style(self, workbook:Workbook, worksheet:Worksheet, df:pd.DataFrame):
        """
        Sets the overall style for the Excel worksheet.

        Args:
            workbook (Workbook): The Excel workbook.
            worksheet (Worksheet): The worksheet being styled.
            df (pd.DataFrame): The DataFrame containing the data.
        """

        header_format = workbook.add_format(self.get_excel_header_format())
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format )
            self.set_excel_column_styles(workbook, worksheet, col_num, value, header_format)

        worksheet.autofilter(0, 0, 0, len(df.columns)-1)

        # max_row, max_col = df.shape

        # worksheet.conditional_format("A2:A7", options={
        #     "type":"3_color_scale",
        #     "min_color": "#1ED760",
        #     "mid_color": "#0088D2",
        #     "max_color": "#A95EFF"
        #     })
        #worksheet.conditional_format("A2:E7", {"format":header_format})


    def get_excel_writer(self, output_bytes:BytesIO, engine:str="xlsxwriter", date_format:str="d/mmm/yyyy", datetime_format:str="d/mmm/yyyy  hh:mm:ss", *args, **kwargs) -> pd.ExcelWriter:
        """
        Returns the Excel writer object.

        Args:
            output_bytes (BytesIO): The output bytes buffer.
            engine (str, optional): The Excel writing engine. Defaults to "xlsxwriter".
            date_format (str, optional): The date format. Defaults to "d/mmm/yyyy".
            datetime_format (str, optional): The datetime format. Defaults to "d/mmm/yyyy  hh:mm:ss".
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            pd.ExcelWriter: The Excel writer object.
        """
        return pd.ExcelWriter(output_bytes, engine=engine,
            date_format=date_format, datetime_format=datetime_format,
            *args, **kwargs
            )
    def generate_excel_file(self, data:QuerySet) -> tuple[bytes, str]:
        """
        Generates an Excel file from a QuerySet using pandas and xlsxwriter.
        It uses a serializer to convert the QuerySet to a list of dictionaries,
        which are then transformed into a pandas DataFrame.
        https://xlsxwriter.readthedocs.io/working_with_pandas.html

        Args:
            data (QuerySet): The QuerySet containing the data to be exported.

        Returns:
            tuple[bytes, str]: A tuple containing the binary data of the Excel file and the filename.
        """
        serializer = self.get_export_serializer(instance=data, many=True)
        serialized_data = serializer.data

        df = pd.DataFrame(serialized_data)
        filename = self.get_filename()

        output_bytes = BytesIO()

        excel_writer = self.get_excel_writer(output_bytes)

        # Write the file in chunks to save memory
        for _, chunk in enumerate(df.groupby(df.index // 10_000)):
            chunk[1].to_excel(excel_writer=excel_writer, index=False, sheet_name=filename, )

        # Style the Excel
        workbook:Workbook = excel_writer.book
        worksheet:Worksheet = excel_writer.sheets[filename]
        self.set_excel_style(workbook, worksheet, df)

        # Close the file
        excel_writer.close()

        excel_data = output_bytes.getvalue()

        return excel_data, filename

    def generate_csv_file(self, data:QuerySet[BaseModel] | list[BaseModel]) -> tuple[bytes, str]:
        """
        Generates a CSV file from the given data.
        
        Args:
            data (QuerySet[BaseModel] | list[BaseModel]): The data to export.

        Returns:
            tuple[bytes, str]: A tuple containing the binary data of the CSV file and the filename.
        """
        serializer = self.get_export_serializer(instance=data, many=True)
        df = pd.DataFrame(serializer.data)
        filename = self.get_filename()
        output_bytes = BytesIO()
        df.to_csv(output_bytes, ';', index=False)
        return output_bytes.getvalue(), filename
    
    # def generate_xml_file(self, data:QuerySet[BaseModel] | list[BaseModel]) -> tuple[bytes, str]:
    #     """Generates a xml file
        
    #     Args:
    #         data (QuerySet[BaseModel] | list[BaseModel]): The data to export

    #     Returns:
    #         tuple[bytes, str]: The xml file and the filename
    #     """
    #     serializer = self.get_export_serializer(instance=data, many=True)
    #     df = pd.DataFrame(serializer.data)
    #     filename = self.get_filename()
    #     output_bytes = BytesIO()
    #     df.to_xml(output_bytes, index=False)
    #     return output_bytes.getvalue(), filename

    def get_file_extension(self, file_format:str) -> str:
        """
        Returns the file extension for the report based on the file format.

        Args:
            file_format (str): The file format (e.g., "excel", "csv").

        Returns:
            str: The file extension (e.g., "xlsx", "csv").
        """
        if file_format == "excel":
            return "xlsx"
        return file_format

    @method_decorator(cache_page(settings.CACHE_LIFETIME) if settings.ACTIVE_CACHE else lambda x: x)
    @action(methods=["GET"], detail=False, url_path="export",)
    def download_report(self, request:Request, *args, **kwargs):
        """
        Exports the data report to Excel or CSV.

        This method is decorated with cache_page to cache the Excel generation with Pandas.

        Args:
            request (Request): The request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: The response containing the exported file or an error message.
        """
        data, status_code = self.get_data(request=request)

        if status_code != status.HTTP_200_OK:
            return Response(data, status_code)

        if "file_format" in request.query_params:
            tipo_formato:str = request.query_params["file_format"].lower()
            
            if not hasattr(self, "generate_%s_file" % tipo_formato):
                return Response(
                    {"message": "This format is not available, only csv, excel"},
                    status.HTTP_400_BAD_REQUEST
                    )
            
            parser_func:Callable[[QuerySet[BaseModel] | list[BaseModel]], tuple[bytes, str]] = getattr(self, "generate_%s_file" % tipo_formato)
            
            file_extension = self.get_file_extension(tipo_formato)
            
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
