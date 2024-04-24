from pathlib import Path
from apps.base.utils import MessageManager as MM
import os

class enumDB:
    POSTGRES = 'postgresql'
    MYSQL = 'mysql'


def get_db_config(db_engine:str = "sqlite", sqlite_path:Path = Path(__file__).resolve().parent.parent) -> dict[str, str]:
    db_properties = {
        'NAME':     os.environ.get('DBNAME'),
        'USER':     os.environ.get('DBUSER'),
        'PASSWORD': os.environ.get('DBPASSWORD'),
        'PORT':     os.environ.get('DBPORT'),
        'HOST':     os.environ.get('DBHOST'),
    }
    
    if db_engine == enumDB.POSTGRES:
        return {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        **db_properties
        }
    elif db_engine == enumDB.MYSQL:
        return {
        'ENGINE': 'django.db.backends.mysql',
        **db_properties
    }
    else:
        MM.warning("Se está usando SQLITE por defecto," + 
                " recuerda establecer las variables de entorno")
        
        if not sqlite_path.exists(): # Si no existe el directorio, lo crea
            sqlite_path.mkdir()
        return {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': sqlite_path / 'db.sqlite3',
    }