from typing import Any
from rest_framework import serializers
from django.db.models import QuerySet, F, Model

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