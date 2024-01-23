from rest_framework import serializers
from .models import User, Customer, CustomerConfig, AccessType
from product.models import TestType
from django.contrib.auth.hashers import make_password

class UserRetriveSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # fields = ['id', 'username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff', 'is_active', 'date_joined', 'last_login']
        exclude = ['password']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        user = User.objects.create(**validated_data)
        return user
    
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class CustomerConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerConfig
        fields = '__all__'

class TestTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestType
        fields = '__all__'

class AccessTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessType
        fields = '__all__'
