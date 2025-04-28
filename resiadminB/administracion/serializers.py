from rest_framework import serializers
from .models import Usuario, WhiteList

class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = Usuario
        fields = ['id', 'email', 'password', 'first_name', 'last_name', 'rut', 'telefono', 'rol']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Usuario(**validated_data)
        user.set_password(password)
        user.save()
        return user

class WhiteListSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhiteList
        fields = ['email', 'estado', 'complejo']
