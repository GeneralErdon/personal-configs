

from typing import Any
from faker import Faker
from rest_framework.response import Response
from django.db.models import Model
from rest_framework import status
from apps.base.models import BaseModel
# Create your tests here.

class BaseFactory:
    faker = Faker()
    model:Model = None
    
    def get_json(self) -> dict[str, str | int | Any]:
        """Genera un Diccionario con el formato que se utilizará para el modelo 
        en cuestión

        Raises:
            NotImplementedwarning: Salta el warning en caso de que no se haya sobreescrito
        """
        raise NotImplementedError("Debe implementar este metodo para usar el factory")
    
    def get_invalid_json(self) -> dict[str, str | int | Any]:
        """Genera un Diccionario con datos errados para los errores de creacion, etc.

        Raises:
            NotImplementedwarning: Salta el warning en caso de que no se haya sobreescrito
        """
        raise NotImplementedError("Debe implementar este metodo para usar el factory")
    
    def get_create_json(self) -> dict[str, str | int | Any]:
        """Genera un diccionario con los datos para
        crear instancias, sobreescribir en caso de 
        especificar llaves foraneas u otras instancias en la creacion
        de relaciones

        Returns:
            dict: Diccionario de instancias y tipos python
        """
        return self.get_json()
    
    
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
        items = [ model_class(**self.get_create_json()) for _ in range(count) ]
        return model_class.objects.bulk_create(items)
    
    def create(self, **overrides) -> Model:
        """Creación individual del item en la base de datos
        
        Se pueden sobreescribir datos en parámetros llave=valor

        Returns:
            Model: Modelo creado
        """
        data = {
            **self.get_create_json(),
            **overrides
        }
        model_class = self.get_model()
        return model_class.objects.create(**data)

class FactoryMixin:
    factory:BaseFactory = None
    endpoint:str = None
    
    def get_factory(self) -> BaseFactory:
        self.assertNotEqual(self.factory, None,"No se ha proporcionado la instancia de factory")
        if isinstance(self.factory, BaseFactory): return self.factory
        self.factory = self.factory()
        return self.factory
    
    def get_endpoint(self) -> str:
        self.assertNotEqual(self.endpoint, None, "No se proporcionó el endpoint")
        return self.endpoint
    
    def get_model(self) -> Model:
        return self.get_factory().get_model()
    
    @property
    def model_name(self) -> str:
        return self.get_model().__name__.upper()


class ReadOnlyTestCaseMixin(FactoryMixin):
    """
    Test case mixin for read only
    """
    def test_listing(self):
        factory = self.get_factory()
        factory.create_bulk(120)
        
        # makes the request
        response:Response = self.client.get(path=self.get_endpoint())
        
        # verify 
        # status code OK
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        
        self.Messages.ok(f"TEST LIST {self.model_name} COMPLETED OK ✅")
    
    def test_retrieve(self):
        factory = self.get_factory()
        obj:Model = factory.create()
        
        response: Response = self.client.get(self.get_endpoint() + f"/{obj.pk}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(obj.pk, response.data["id"])
        
        self.Messages.ok(f"TEST RETRIEVE {self.model_name} COMPLETED OK ✅")


class CreateTestCaseMixin(FactoryMixin):
    """
    Test case mixin for create
    """
    def test_create(self):
        factory = self.get_factory()
        create_data = factory.get_json()
        
        response: Response = self.client.post(self.get_endpoint() + "/", data=create_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        
        # Verify the creation of the object
        for key, value in create_data.items():
            try:
                self.assertEqual(response.data[key], value)
            except KeyError:
                continue
        
        # Optionally, verify the object exists in the database
        created_object = self.get_model().objects.filter(pk=response.data["id"]).first()
        self.assertIsNotNone(created_object)
        
        self.Messages.ok(f"TEST CREATE {self.model_name} COMPLETED OK ✅")


class UpdateTestCaseMixin(FactoryMixin):
    """
    Test case mixin for update
    """
    def test_update(self):
        factory = self.get_factory()
        obj: Model = factory.create()
        update_data = factory.get_json()
        
        response: Response = self.client.put(self.get_endpoint() + f"/{obj.pk}/", data=update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        
        # Verify the updated fields
        for key, value in update_data.items():
            try:
                self.assertEqual(response.data[key], value)
            except KeyError:
                continue
        
        self.Messages.ok(f"TEST UPDATE {self.model_name} COMPLETED OK ✅")
    
    def test_patch(self):
        factory = self.get_factory()
        obj: Model = factory.create()
        patch_data = factory.get_json()
        
        response: Response = self.client.patch(self.get_endpoint() + f"/{obj.pk}/", data=patch_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        
        # Verify the patched fields
        for key, value in patch_data.items():
            try:
                self.assertEqual(response.data[key], value)
            except KeyError:
                continue
        
        self.Messages.ok(f"TEST PATCH {self.model_name} COMPLETED OK ✅")


class DeleteTestCaseMixin(FactoryMixin):
    """
    Test case mixin for delete
    """
    def test_delete(self):
        factory = self.get_factory()
        obj: BaseModel = factory.create()
        
        response: Response = self.client.delete(self.get_endpoint() + f"/{obj.pk}/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify logical deletion (status = False)
        obj.refresh_from_db()
        self.assertEqual(obj.status, obj.deactivated_status, response.data)
        
        self.Messages.ok(f"TEST DELETE (LOGICAL) {self.model_name} COMPLETED OK ✅")


class ReadOnlyErrorTestCaseMixin(FactoryMixin):
    """
    Test case mixin for read only errors
    """
    def test_retrieve_not_found(self):
        non_existent_id = 999999  # Un ID que no existe en la base de datos
        
        response: Response = self.client.get(self.get_endpoint() + f"/{non_existent_id}/")
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.data)
        self.assertIn("message", response.data, "No se ha incluido el key de message")
        
        self.Messages.ok(f"TEST RETRIEVE NOT FOUND {self.model_name} COMPLETED OK ✅")
    
    def test_method_not_allowed(self):
        response: Response = self.client.put(self.get_endpoint() + "/", data={})
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED, response.data)
        self.Messages.ok(f"TEST METHOD NOT ALLOWED {self.model_name} COMPLETED OK ✅")

class CreateErrorTestCaseMixin(FactoryMixin):
    """
    Test case mixin for create errors
    """
    def test_create_bad_request(self):
        factory = self.get_factory()
        invalid_data = factory.get_invalid_json()  # Debes definir este método en tu factory
        
        response: Response = self.client.post(self.get_endpoint() + "/", data=invalid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("message", response.data, "No se ha incluido el key de message")
        
        self.Messages.ok(f"TEST CREATE BAD REQUEST {self.model_name} COMPLETED OK ✅")

class UpdateErrorTestCaseMixin(FactoryMixin):
    """
    Test case mixin for update errors
    """
    def test_update_bad_request(self):
        factory = self.get_factory()
        obj: Model = factory.create()
        invalid_data = factory.get_invalid_json()
        
        response: Response = self.client.put(self.get_endpoint() + f"/{obj.pk}/", data=invalid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("message", response.data, "No se ha incluido el key de message")
        
        self.Messages.ok(f"TEST UPDATE BAD REQUEST {self.model_name} COMPLETED OK ✅")

class DeleteErrorTestCaseMixin(FactoryMixin):
    """
    Test case mixin for delete errors
    """
    def test_delete_not_found(self):
        non_existent_id = 999999
        
        response: Response = self.client.delete(self.get_endpoint() + f"/{non_existent_id}/")
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.data)
        self.assertIn("message", response.data, "No se ha incluido el key de message")
        
        self.Messages.ok(f"TEST DELETE NOT FOUND {self.model_name} COMPLETED OK ✅")

class CRUDErrorTestCaseMixin(
        ReadOnlyErrorTestCaseMixin,
        CreateErrorTestCaseMixin,
        UpdateErrorTestCaseMixin,
        DeleteErrorTestCaseMixin
    ):
    """
    Test case mixin for CRUD errors
    """
    pass

class CRUDTestCaseMixin(
        ReadOnlyTestCaseMixin,
        CreateTestCaseMixin,
        UpdateTestCaseMixin,
        DeleteTestCaseMixin,
        CRUDErrorTestCaseMixin
    ):
    """
    Test case mixin for CRUD
    """
    pass

class ReadOnlyTestCaseMixin(ReadOnlyTestCaseMixin, ReadOnlyErrorTestCaseMixin):
    """
    Test case mixin for Read Only
    """
    pass
    
    # =========== error 401 (Unauthorized) ============
    # def test_unauthorized(self):
    #     self.client.logout()  # Asegúrate de que el cliente no esté autenticado
        
    #     response: Response = self.client.get(self.get_endpoint())
        
    #     self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, response.data)
    #     self.assertIn("message", response.data, "No se ha incluido el key de message")
        
    #     self.Messages.ok("TEST UNAUTHORIZED COMPLETED OK ✅")
    
    # =========== error 403 (Forbidden) ============
    # def test_forbidden(self):
    #     # Simular una acción que el usuario actual no tiene permiso para realizar
    #     factory = self.get_factory()
    #     obj: Model = factory.create()
        
    #     response: Response = self.client.delete(self.get_endpoint() + f"/{obj.pk}/")
        
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)
    #     self.assertEqual(response.data["message"], "Prohibido")
        
    #     self.Messages.ok("TEST FORBIDDEN COMPLETED OK ✅")