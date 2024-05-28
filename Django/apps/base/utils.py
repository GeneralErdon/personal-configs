from typing import Any, Callable
import pika
import json
from environ import Env
import datetime as dt

from apps.base.types import PikaCallback_T


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


class RabbitMQManager:
    """Clase para el manejo de las conexiones con rabbitMQ
    para funciones de messageBroker.
    
    se utiliza para visualización de mensajes en las colas
    de eventos y publicación de mensajes.
    """
    def __init__(self):
        self.connection = None
        self.channel = None

    def connect(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=env.str("RABBITMQ_HOST"),
                port=env.str("RABBITMQ_PORT"),
                credentials=pika.PlainCredentials(
                    username=env.str("RABBITMQ_USER"),
                    password=env.str("RABBITMQ_PASSWORD"),
                ),
            )
        )
        
        self.channel = self.connection.channel()

    def close(self):
        if self.connection:
            self.connection.close()

    def publish(self, queue_name:str, message:dict[str, Any]):
        """Función para publicar un mensaje en una queue de eventos
        Args:
            queue_name (str): Nombre de la queue
            message (dict[str, Any]): Mensaje o datos para publicar.
        """
        if not self.connection or self.connection.is_closed:
            self.connect()
        
        
        self.channel.queue_declare(queue=queue_name, durable=True)
        self.channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)
        )
    
    def find_message_with_id(self, queue_name:str, obj_id:int, auto_ack:bool=True, comparator_func:Callable[[int, dict[str, Any] | Any], bool] = lambda i, m: i == m["id"], callback:PikaCallback_T|None = None) -> Any | None:
        """Funcion para buscar especificamente un mensaje de evento
        en las colas de rabbitMQ mediante la ID de un elemento en el Body.
        Cabe destacar que este elemento en el Body debe ser un formato Json 
        de un diccionario por lo menos. No una lista de Json.
        
        Recuerda luego de llamar a esta función llamar a rabit_mq.close() para que cuando 
        se vuelva a ejecutar empiece a ver otra vez la cola.

        Args:
            queue_name (str): Nombre de la cola a buscar el elemento
            obj_id (int): Id del objetivo que se va a buscar en el mensaje
            auto_ack (bool): Especifica si hace un basic_ack justo antes de terminar esta funcion.
            comparator_func (Callable[[int, dict[str, Any]  |  Any], bool], optional): Criterio de búsqueda opcional
                Por defecto tiene una funcion lambda que compara el id con el id del json del mensaje
                pero la idea es especificar una funcion que retorne un bool y haga una 
                comparacion entre el contenido del mensaje y el obejtivo de busqueda. 
                Defaults to lambda i, m (i, optional): Defaults to =m["id"].
            callback (PikaCallback_T | None, optional): Funcion de callback para ejecutar una vez que ya
            se ha encontrado el mensaje. Defaults to None.

        Returns:
            Any | None: Retorna el mensaje ya cargado en objeto python si lo encontró
            None en caso contrario
        """
        if not self.connection or self.connection.is_closed:
            self.connect()
        
        self.channel.queue_declare(queue=queue_name, durable=True)
        
        while True:
            method_frame, properties, body = self.channel.basic_get(queue_name)
            if method_frame is None:
                # si no encuentra nada, break
                break
            message:dict[str, Any] = json.loads(body)
            if comparator_func(obj_id, message):
                if callback is not None:
                    callback(self.channel, method_frame, properties, body)
                # Confirma que se procesó el mensaje correctamente
                if auto_ack:
                    self.channel.basic_ack(method_frame.delivery_tag)
                return message
            
            # No es el mensaje que busco, re meto en la cola
            # self.channel.basic_nack(method_frame.delivery_tag, requeue=True)
        
        return None

    def consume(self, queue_name:str, callback:PikaCallback_T):
        """Funcion para escuchar constantemente por eventos en una cola de eventos
        utilizado para comunicar en tiempo real

        Args:
            queue_name (str): nombre de la cola
            callback (Callable): Funcion para ejecutar una vez pase un evento
        """
        if not self.connection or self.connection.is_closed:
            self.connect()
        self.channel.queue_declare(queue=queue_name, durable=True)
        # consumo constante
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
        self.channel.start_consuming()