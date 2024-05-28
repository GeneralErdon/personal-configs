from typing import Callable, Any
import pika
from pika.spec import Basic, BasicProperties
from pika.adapters.blocking_connection import  BlockingChannel

PikaCallback_T = Callable[
    [ # Argumentos
        BlockingChannel,
        Basic.Deliver,
        BasicProperties,
        bytes
    ]
    , Any] # return