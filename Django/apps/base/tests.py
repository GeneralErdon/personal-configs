

from faker import Faker
from django.db.models import Model
# Create your tests here.

class BaseFactory:
    faker = Faker()
    model:Model = None
    
    def get_json(self):
        """Genera un Diccionario con el formato que se utilizará para el modelo 
        en cuestión

        Raises:
            NotImplementedError: Salta el error en caso de que no se haya sobreescrito
        """
        raise NotImplementedError("Debe implementar este metodo para usar el factory")
    
    def get_model(self) -> Model:
        assert self.model is not None, "No se ha especificado el modelo del factory"
        return self.model
    
    def create_bulk(self, count:int) -> list[Model]:
        """Método para la creación masiva de items en una sola consulta

        Args:
            count (int): Cantidad de items a crear

        Returns:
            list[Model]: Modelos creados
        """
        model_class = self.get_model()
        items = [ model_class(**self.get_json()) for _ in range(count) ]
        return model_class.objects.bulk_create(items)
    
    def create(self, **overrides) -> Model:
        """Creación individual del item en la base de datos
        
        Se pueden sobreescribir datos en parámetros llave=valor

        Returns:
            Model: Modelo creado
        """
        data = {
            **self.get_json(),
            **overrides
        }
        model_class = self.get_model()
        return model_class.objects.create(**data)