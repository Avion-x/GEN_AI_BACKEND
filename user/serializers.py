from rest_framework import serializers
from .models import User, Customer, CustomerConfig, AccessType
from product.models import TestType
from django.contrib.auth.hashers import make_password
import pytz


class ISTTimestamp:
    def get_ist_timestamp(self, timestamp):
        utc_timestamp = timestamp.astimezone(pytz.utc)
        ist_timestamp = utc_timestamp.astimezone(pytz.timezone('Asia/Kolkata'))
        formatted_timestamp = ist_timestamp.strftime("%Y-%m-%d %H:%M")
        return formatted_timestamp


class UserRetriveSerializer(serializers.ModelSerializer, ISTTimestamp):
    created_at = serializers.SerializerMethodField()
    last_updated_at = serializers.SerializerMethodField()
    last_login = serializers.SerializerMethodField()
    date_joined = serializers.SerializerMethodField()

    class Meta:
        model = User
        # fields = ['id', 'username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff', 'is_active', 'date_joined', 'last_login']
        exclude = ['password']

    def get_created_at(self,obj):
        timestamp = obj.created_at
        ist_timestamp = self.get_ist_timestamp(timestamp)
        return ist_timestamp
    
    def get_last_updated_at(self,obj):
        timestamp = obj.last_updated_at
        ist_timestamp = self.get_ist_timestamp(timestamp)
        return ist_timestamp
    
    def get_date_joined(self,obj):
        timestamp = obj.date_joined
        ist_timestamp = self.get_ist_timestamp(timestamp)
        return ist_timestamp
    
    def get_last_login(self,obj):
        if obj.last_login:
            timestamp = obj.last_login
            ist_timestamp = self.get_ist_timestamp(timestamp)
            return ist_timestamp
        else:
            return obj.last_login
    

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

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
