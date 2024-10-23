from channels.layers import get_channel_layer
from channels_redis.core import RedisChannelLayer
from asgiref.sync import async_to_sync
import json
from typing import List, Union
from apps.human_resources.employees.models import Employee
from apps.users.models import User

class NotificationService:
    TYPE_SEND_NOTIFICATION = "send_notification"
    
    @staticmethod
    def send_notification(recipient:User, message: str | dict):
        """
        Envia una notificación al usuario especificado.

        Args:
            recipient (User): El usuario al que se enviará la notificación.
            message (str | dict): El mensaje de la notificación.
        """
        channel_layer: RedisChannelLayer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{recipient.id}",
            {
                "type": NotificationService.TYPE_SEND_NOTIFICATION,
                "message": message,
            }
        )
    
    @classmethod
    def send_multiple_notification(cls, recipients:List[User], message:str | dict):
        """
        Envia una notificación a varios usuarios.

        Args:
            recipients (List[User]): Los usuarios a los que se enviará la notificación.
            message (str | dict): El mensaje de la notificación.
        """
        for recipient in recipients:
            cls.send_notification(recipient, message)
    
    @classmethod
    def notify_all_users(cls, message: str | dict):
        users = User.objects.all()
        cls.send_multiple_notification(users, message)
    @classmethod
    def notify_department(cls, department_id: int, message: str, notification_type: str):
        employees = Employee.objects.filter(company__department__id=department_id)
        cls.send_multiple_notification(employees, message, notification_type)

    @classmethod
    def notify_employee_and_manager(cls, employee_id: int, message: str, notification_type: str):
        employee = Employee.objects.get(id=employee_id)
        recipients = [employee]
        if employee.manager:
            recipients.append(employee.manager)
        cls.send_multiple_notification(recipients, message, notification_type)
