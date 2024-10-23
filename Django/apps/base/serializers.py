from typing import Any
from rest_framework import serializers
from rest_framework.utils import model_meta
from django.db.models import QuerySet, F, Model
import datetime as dt
from apps.base.models import BaseModel
from apps.users.models import User
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class GenericReadOnlySerializer(serializers.ModelSerializer):
    
    def get_fields(self, *args, **kwargs):
        """Crear los campos como Read Only optimiza la serialización de datos
        este método es para hacer que todos los fields sean readOnly
        """
        fields = super().get_fields(*args, **kwargs)
        for field in fields:
            fields[field].read_only = True
        return fields
    def _format_date(self, date:dt.date | None) -> str | None:
        """Formats the date to a pretty format like:
        12 of June 2024

        Args:
            date (dt.datetime | None): Date to format

        Returns:
            str: Pretty formatted date or None if date is None
        """
        if date:
            return date.strftime("%d of %B %Y").capitalize()
        return None
    def _format_datetime(self, date:dt.datetime | None) -> str | None:
        """Formats the date to a pretty format like:
        12 of June 2024 at 12:00 hours

        Args:
            date (dt.datetime | None): Date to format

        Returns:
            str: Pretty formatted date or None if date is None
        """
        if date:
            return date.strftime("%d of %B %Y at %H:%M hours").capitalize()
        return None

class BaseReadOnlySerializer(GenericReadOnlySerializer):
    """Read Only serializer that applies read only to all fields for improve serialization and formats dates
    """
    created_date = serializers.DateTimeField(format="%d-%m-%Y %H:%M:%S", read_only=True)
    modified_date = serializers.DateTimeField(format="%d-%m-%Y %H:%M:%S", read_only=True)
    deleted_date = serializers.DateTimeField(format="%d-%m-%Y %H:%M:%S", read_only=True)
    pretty_created_date = serializers.SerializerMethodField()
    pretty_modified_date = serializers.SerializerMethodField()
    pretty_deleted_date = serializers.SerializerMethodField()
    
    

    def get_pretty_created_date(self, obj: BaseModel) -> str:
        return self._format_datetime(obj.created_date)
    
    def get_pretty_modified_date(self, obj: BaseModel) -> str:
        return self._format_datetime(obj.modified_date)
    
    def get_pretty_deleted_date(self, obj: BaseModel) -> str:
        return self._format_datetime(obj.deleted_date)
    
    


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
    
    def get_fields_info(self):
        """This function returns the FieldInfo of the model of this serializer

        Returns:
            FieldInfo: This instance help to know the fields and relationships of this model
        """
        model = self.get_model()
        info = model_meta.get_field_info(model)
        return info
    
    
    
    def validate(self, attrs:dict[str, Any]) -> dict[str, Any]:
        """
        Returns:
            dict[str, Any]: Returns the validated data
        """
        
        user:User | None = self.context.get("request").user
        if user is None:
            raise ValidationError(_("User not found"))
        attrs["changed_by"] = user
        return attrs

    @property
    def manual_fields(self) -> list[str]:
        """
        This property is used to get the m2m fields or fields that I want to handle manually
        for example: "bank_account" is not a m2m field but a related field, so I need to handle it manually
        in the update method
        
        and "titles" and "departments" are m2m fields that have Through table and I need to handle it manually
        in the update method

        Returns:
            list[str]: The list of m2m fields with custom update methods or manual fields OF THIS SERIALIZER
        """
        
        return []
    
    
    def handle_manual_fields(self, instance: BaseModel, data: dict[str, Any], validated_data: dict[str, Any] | None = None) -> BaseModel:
        """
        This function is for update the m2m items of this instance

        Args:
            instance (BaseModel): Model instance
            data (dict[str, Any]): Data to update
            validated_data (dict[str, Any] | None, optional): Validated data. Defaults to None.
        """
        for field, value in data.items():
            if value:
                callback = getattr(self, f"create_{field}")
                callback(instance, value)
    
    def get_manual_fields(self, validated_data: dict[str, Any]) -> dict[str, Any]:
        """
        Returns:
            dict[str, Any]: Returns a dictionary with the fields as keys and the values as values
        """
        fields = {}
        for field in self.manual_fields:
            assert getattr(self, f"create_{field}", None) is not None, f"The method create_{field} does not exist"
            fields[field] = validated_data.pop(field, None)
        return fields
    
    def create(self, validated_data: dict[str, Any]) -> BaseModel:
        popped_fields = self.get_manual_fields(validated_data)
        instance = super().create(validated_data)
        self.handle_manual_fields(instance, popped_fields)
        return instance

class BaseUpdateSerializer(BaseModelSerializer):
    """
    Update Serializer for handle updates and M2M updates
    """
    
    def get_manual_fields(self, validated_data: dict[str, Any]) -> dict[str, Any]:
        """
        Returns:
            dict[str, Any]: Returns a dictionary with the fields as keys and the values as values
        """
        fields = {}
        for field in self.manual_fields:
            assert getattr(self, f"update_{field}", None) is not None, f"The method update_{field} does not exist"
            fields[field] = validated_data.pop(field, None)
        return fields
    
    def handle_manual_fields(self, instance: BaseModel, data: dict[str, Any], validated_data: dict[str, Any] | None = None) -> BaseModel:
        """
        This function is for update the m2m items of this instance

        Args:
            instance (BaseModel): Model instance
            data (dict[str, Any]): Data to update
            validated_data (dict[str, Any] | None, optional): Validated data. Defaults to None.
        """
        for field, value in data.items():
            if value:
                callback = getattr(self, f"update_{field}")
                callback(instance, value)
    
    def set_m2m_field(self,instance:BaseModel, field:Any, key: str, value:list[Any]):
        """Override this function for m2m through tables defaults
        maybe with 
        field.set(values, through_defaults=...)

        Args:
            field (ManyToManyRelatedManager[BaseModel]): Field M2M to be overrided
            value (list[Any]): Values to set
        """
        field.set(value)
    def update_m2m_items(self, instance:BaseModel, m2m_fields:list[tuple[str, Any]] ):
        """This function is for update the m2m items of this instance

        Args:
            instance (BaseModel): Model instance
            m2m_fields (list[tuple[str, Any]]): Values with key, m2m items
        """
        # Note that many-to-many fields are set after updating instance.
        # Setting m2m fields triggers signals which could potentially change
        # updated instance and we do not want it to collide with .update()
        for attr, value in m2m_fields:
            field = getattr(instance, attr)
            self.set_m2m_field(instance, field, attr, value)
        
        
    def update(self, instance:BaseModel, validated_data: dict[str, Any]) -> BaseModel:
        
        popped_fields = self.get_manual_fields(validated_data)
        
        # Update the basic fields and collect the m2m relations
        info = self.get_fields_info()
        m2m_fields:list[tuple[str, Any]] = []
        for key, value in validated_data.items():
            if key in info.relations and info.relations[key].to_many:
                m2m_fields.append((key, value))
            else:
                setattr(instance, key, value)
        
        instance.save()
        self.update_m2m_items(instance, m2m_fields)
        
        # Handle the manually handled fields
        self.handle_manual_fields(instance, popped_fields)
        return instance
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