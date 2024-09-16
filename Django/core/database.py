from pathlib import Path
from apps.base.utils import MessageManager as MM
import os


POSTGRES = 'postgresql'


def get_db_config(db_engine:str = "sqlite", sqlite_path:Path = Path(__file__).resolve().parent.parent) -> dict[str, str]:
    db_properties = {
        'NAME':     os.environ.get('POSTGRES_DB'),
        'USER':     os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'PORT':     os.environ.get('POSTGRES_PORT'),
        'HOST':     os.environ.get('POSTGRES_HOST'),
    }
    
    if db_engine == POSTGRES:
        db_properties['ENGINE'] = 'django.db.backends.postgresql_psycopg2'
        return db_properties
    # Acá se podría añadir la config de mysql u otros...
    
    # Utiliza sqlite si no se estableció que se utilice postgresql
    MM.warning(("Se está usando SQLITE por defecto, "
                "recuerda establecer las variables de entorno"))
    
    if not sqlite_path.exists(): # Si no existe el directorio, lo crea
        sqlite_path.mkdir()
    return {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': sqlite_path / 'db.sqlite3',
    }