from environ import Env
import datetime as dt
from django.utils import timezone

env:Env = Env()

def calcular_edad(birth_date:dt.date) -> int:
    # Calculamos la edad actual
    fecha_actual = timezone.now()
    edad = fecha_actual.year - birth_date.year - ((fecha_actual.month, fecha_actual.day) < (birth_date.month, birth_date.day))
    return edad

def get_birth_date_from_age(age:int) -> dt.date:
    fecha_actual = timezone.now()
    return fecha_actual.year - age


class MessageManager:
    OKGREEN = '\033[92m'
    OKBLUE = '\033[94m'
    ERROR = '\033[91m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'
    
    @staticmethod
    def warning(message:str):
        """
        Print a warning message with color orange on terminal
        """
        print(MessageManager.WARNING, message, MessageManager.ENDC)
    
    @staticmethod
    def ok(message:str):
        """
        Print a success message with color green on terminal
        """
        print(MessageManager.OKGREEN, message, MessageManager.ENDC)
    
    @staticmethod
    def error(message:str):
        """
        Print a error message with color red on terminal
        """
        print(MessageManager.ERROR, message, MessageManager.ENDC)
    
    @staticmethod
    def okblue(message:str):
        """
        Print a success message with color blue on terminal
        """
        print(MessageManager.OKBLUE, message, MessageManager.ENDC)

