from apps.base.tests import BaseFactory, CRUDTestCaseMixin
from apps.users.models import User
from django.db.models import Model
from rest_framework import status
from rest_framework.response import Response
from tests.factories.users.user_factory import UsersFactory
from tests.test_setup import TestSetup
import json



    

class UserTestCase(CRUDTestCaseMixin, TestSetup):
    factory = UsersFactory()
    endpoint = "/user"
    
