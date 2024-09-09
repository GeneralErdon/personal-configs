from datetime import datetime
from django.contrib.auth import authenticate
from django.contrib.sessions.models import Session
from rest_framework import status,generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi as op
from apps.users.api.serializers.token_obtain import CustomTokenObtainPairSerializer
from apps.users.api.serializers.user_serializers import UserReadOnlySerializer, UserSerializer
from apps.users.models import User

# Create your views here.
class Login(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request: Request, *args, **kwargs) -> Response:
        username = request.data.get("username", None)
        password = request.data.get("password", None)
        user: User = authenticate(
            username=username,
            password=password,
        )
        if user is not None:
            login_serializer = self.get_serializer(data=request.data)
            if login_serializer.is_valid():
                if not user.is_active:
                    return Response(
                        {"message": "Este usuario no puede iniciar sesión"},
                        status=status.HTTP_401_UNAUTHORIZED)
                user_serializer = UserReadOnlySerializer(instance=user)
                return Response({
                    "token": login_serializer.validated_data.get("access"),
                    "refresh-token": login_serializer.validated_data.get("refresh"),
                    "user": user_serializer.data,
                })
        return Response(
            {"message": "Usuario o contraseña incorrectos"},
            status=status.HTTP_400_BAD_REQUEST)

class Logout(generics.GenericAPIView):
    permission_classes = [IsAuthenticated,]
    
    
    def delete_all_sessions(self, user:User) -> None:
        all_sessions = Session.objects.filter(expire_date__gte=datetime.now())
        if all_sessions.exists():
            for session in all_sessions:
                session_data = session.get_decoded()
                if user.id == int(session_data.get("_auth_user_id")):
                    session.delete()
        
    
    
    @swagger_auto_schema(
        request_body=None,
        responses={
            status.HTTP_200_OK: op.Response(
                description="Logout correcto",
                schema=op.Schema(
                        type=op.TYPE_OBJECT,
                        properties={"message": op.Schema(type=op.TYPE_STRING)},
                    )
                )
        }
    )
    def post(self, request:Request, *args, **kwargs):
        
        user: User = request.user
        if user is not None:
            RefreshToken.for_user(user=user)
            
            # Si deseo cerrar el resto de sesiones, descomenta la sig linea
            self.delete_all_sessions(user)
            
            return Response({
                "message": "Se ha cerrado la sesión"
            }, status.HTTP_200_OK)
        
        return Response({"message": "El usuario no existe"}, status.HTTP_400_BAD_REQUEST)