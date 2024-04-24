
from typing import TypedDict


class _TUserValidatedData(TypedDict):
    username: str
    password: str
    email: str
    is_superuser: bool
    is_staff: bool
    groups: list[str]
    user_permissions: list[str]
    
    