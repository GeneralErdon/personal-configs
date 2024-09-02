from typing import Any
from rest_framework import serializers
from django.db.models import QuerySet, F, Model

from apps.base.models import BaseModel


class BaseReadOnlySerializer(serializers.ModelSerializer):
    """Read Only serializer that applies read only to all fields for improve serialization and formats dates
    """
    created_date = serializers.DateTimeField(format="%d-%m-%Y %H:%M:%S", read_only=True)
    modified_date = serializers.DateTimeField(format="%d-%m-%Y %H:%M:%S", read_only=True)
    deleted_date = serializers.DateTimeField(format="%d-%m-%Y %H:%M:%S", read_only=True)
    
    def get_fields(self, *args, **kwargs):
        """Crear los campos como Read Only optimiza la serialización de datos
        este método es para hacer que todos los fields sean readOnly
        """
        fields = super().get_fields(*args, **kwargs)
        for field in fields:
            fields[field].read_only = True
        return fields


class BaseModelSerializer(serializers.ModelSerializer):
    """Base model serializer
    """
    
    def get_model(self) -> BaseModel.__class__:
        """
        Returns:
            BaseModel: Returns the class, not instance of the model
        """
        return self.Meta.model
    
    def get_unique_fields(self) -> list[str]:
        """
        Returns:
            list[str]: Returns the name of the unique fields in a list
        """
        model = self.get_model()
        # Los many to many Rel no tienen Unique property
        return [x.name for x in model._meta.get_fields() if getattr(x, 'unique', False)] 
        
    
    def unique_field_validation(self, attrs:dict):
        """Makes a query if there's any unique value that exists in the database.

        Args:
            attrs (dict): The attrs to be validated with key(field) and value

        Raises:
            serializers.ValidationError: If there's any repeated unique value
        """
        unique_fields: list[str] = self.get_unique_fields()
        if not unique_fields: return # if empty then close
        for k, v in attrs.items():
            if k not in unique_fields: continue
            
            filter_param = {f"{k}__iexact":v} if isinstance(v, str) else {k:v}
            if self.get_model().objects.filter(**filter_param).exists():
                raise serializers.ValidationError(
                    {k:f'Ya existe este valor único.'})
        
    
    def validate(self, attrs):
        self.unique_field_validation(attrs)
        return super().validate(attrs)

class SQLSerializer:
    def __init__(self, instance:QuerySet|Any, many=True,) -> None:
        self._instance = instance
        self.many = many
        self._data = None
        self._expressions = None
    
    class Meta:
        """
        los Fields deberían ser una estructura
        de diccionario, donde 
        
        campo_deseado : F() | str => FieldName
        """
        model = None
        fields_custom:dict = None
        fields:list = None
    
    @property
    def instance(self,) -> QuerySet | Model:
        return self._instance
    
    @property
    def data(self) -> list[dict] | dict:
        if self._data is None:
            self._data = self.get_serialized_data()
        
        return self._data
    
    @property
    def expressions(self) -> dict[str, F]:
        if self._expressions is None:
            self._expressions = self.transform_custom_fields()
        
        return self._expressions
    
    def transform_custom_fields(self) -> dict[str, F]:
        """Función para transformar los Fields de la propiedad Meta
        de fields.
        si el diccionario contiene un valor de sólo un string, lo convierte en F()
        para representar un Field.

        Returns:
            dict[str, F]: Retorna el nombre del campo nuevo, con la expresión donde sacará el valor.
        """
        annotate_params = {}
        fields_items:list[tuple[str, str|F]] = self.Meta.fields_custom.items()
        
        
        for key, value in fields_items:
            
            if isinstance(value, str):
                value = F(value)
            
            annotate_params[key] = value
            
        
        return annotate_params
    
    
    def get_column_order(self) -> list[str]:
        """En este orden se basará el resultado. debe retornar una Lista con los nombres de los campos.

        Returns:
            list[str]: Lista de String con nombres de los campos
        """
        columns = [*self.Meta.fields ,*self.Meta.fields_custom.keys()]
        return columns
    
    def get_serialized_data(self) -> list[dict] | dict:
        """Obtiene la serialización de la data mediante consulta SQL
        utilizando annotate y Values().

        Returns:
            list[dict] | dict: Datos serializados.
        """
        columns = self.get_column_order()
        
        if self.many:
            
            values = self.instance.annotate(**self.expressions) \
                        .values(*columns)
            
            return values
        
        model = self.Meta.model
        
        
        return model.objects.filter(pk = self.instance.pk).annotate(**self.expressions) \
                .values(*columns).first()