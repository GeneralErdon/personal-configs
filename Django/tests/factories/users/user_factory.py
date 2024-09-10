

from typing import Any
from faker import Faker
from apps.base.tests import BaseFactory
from apps.users.models import User

class UsersFactory(BaseFactory):
    model = User
    
    def get_json(self) -> dict[str, str]:
        f_name = self.faker.first_name().lower()
        l_name = self.faker.last_name().lower()
        
        return {
            "username": f_name[:3] + l_name[:3] + self.faker.email()[:3],
            "password": "developer123",
            "email": self.faker.email(),
            "role": self.faker.random.choice(["M", "A", "E"]),
            "is_staff": False,
            "is_superuser": False,
        }
    
    def get_invalid_json(self) -> dict[str, str | int | Any]:
        return {
            "role": "G",
            "username": "pepe",
            "password": "developer123",
            "is_staff": False,
            "is_superuser": False,
        }