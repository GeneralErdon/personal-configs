from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Clase para sobreescribir el serializador de Usuario
    especialmente diseñado para los tokens
    """
    pass