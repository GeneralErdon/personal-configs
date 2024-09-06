from environ import Env
import datetime as dt


env:Env = Env()

def calcular_edad(birth_date:dt.date) -> int:
    # Calculamos la edad actual
    fecha_actual = dt.datetime.today()
    edad = fecha_actual.year - birth_date.year - ((fecha_actual.month, fecha_actual.day) < (birth_date.month, birth_date.day))
    return edad


class MessageManager:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'
    
    @staticmethod
    def warning(message:str):
        print(MessageManager.WARNING, message, MessageManager.ENDC)
    
    @staticmethod
    def ok(message:str):
        print(MessageManager.OKGREEN, message, MessageManager.ENDC)
    
    @staticmethod
    def error(message:str):
        raise NotImplementedError()

