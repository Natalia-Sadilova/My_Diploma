from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.validators import EmailValidator
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения данных пользователя"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'type', 'company', 'position', 'is_active'
        ]
        read_only_fields = ['id', 'is_active']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class RegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True, validators=[EmailValidator()])
    
    class Meta:
        model = User
        fields = [
            'email', 'username', 'password', 'password2', 
            'first_name', 'last_name', 'type', 'company', 'position'
        ]
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")
        return value
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Пользователь с таким именем уже существует")
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        user.is_active = False
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Сериализатор для входа"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class UserUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления профиля"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'company', 'position']
    
    def validate_username(self, value):
        if User.objects.exclude(id=self.instance.id).filter(username=value).exists():
            raise serializers.ValidationError("Это имя пользователя уже занято")
        return value