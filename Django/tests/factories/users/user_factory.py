

from faker import Faker
from apps.users.models import User

class UsersFactory:
    faker = Faker()
    
    
    def get_user_json(self) -> dict[str, str]:
        f_name = self.faker.first_name().lower()
        l_name = self.faker.last_name().lower()
        
        return {
            "username": f_name[:3] + l_name[:3] + self.faker.email()[:3],
            "password": "developer123",
            "email": self.faker.email(),
            "is_staff": False,
            "is_superuser": False,
        }
    
    def create_bulk_users(self, count:int) -> list[User]:
        users = [ User(**self.get_user_json()) for _ in range(count) ]
        return User.objects.bulk_create(users)
    
    def create_user(self, **extrafields) -> User:
        data = self.get_user_json()
        data = {
            **data,
            **extrafields,
        }
        
        return User.objects.create_user(**data)