from rest_framework import generics, viewsets,permissions, authentication, filters as rest_filters, status
from django_filters import rest_framework as django_filters
from rest_framework.response import Response
from django.db import IntegrityError
from django.contrib.auth.models import Group, Permission
from user.filters import CustomUserFilter, CustomerFilter
from .models import User, Customer, CustomerConfig, AccessType, Roles
from product.models import TestType
from .serializers import UserRetriveSerializer, UserSerializer, CustomerSerializer, CustomerConfigSerializer, TestTypeSerializer, AccessTypeSerializer
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from user.permissions import get_user_permissions
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from django.http import HttpResponse, JsonResponse


def get_request_body(request):
    try:
        return json.loads(request.body.encode('utf-8'))
    except Exception as e:
        print(f"unable to get request body from request. Error is {e}")
        return {}


class LoginView(generics.RetrieveAPIView):
    authentication_classes = (BasicAuthentication,)

    @method_decorator(csrf_exempt)
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            permissions_json = get_user_permissions(username)
            print(permissions_json)
            token, created = Token.objects.get_or_create(user=request.user)
            serializer = UserRetriveSerializer(user)
            return Response({'token': token.key, 'user_details':serializer.data, 'permissions': permissions_json})
        else:
            # Authentication failed
            return Response({'error': 'Invalid credentials'})


class LogoutView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        logout(request)
        return Response({"Action":'success', "Message":'User logged out successfully'})
    

class UserView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend, rest_filters.OrderingFilter)
    filterset_class = CustomUserFilter
    serializer_class = UserSerializer

    ordering_fields = ['id', 'date_joined', 'last_login'] #for ordering or sorting replace with '__all__' for all fields 
    ordering = [] # for default orderings

    def get_role_id(self, role_name):
        return Roles.objects.get(name=role_name).id

    def get_queryset(self, filters={}):
        return User.objects.filter(**filters)

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset().order_by('first_name'))
        serializer = UserRetriveSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if 'customer' not in request.data:
            request.data['customer'] = request.user.customer.id
        request.data['last_updated_by'] = request.user.username
        role_name = request.data.get('role_name')
        role_id = self.get_role_id(role_name)
        if role_id is None:
            return Response({"error": "Role with the provided name does not exist"})
        request.data['role'] = role_id
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "User created successfully", "data": serializer.data, "status": 200})

    def put(self, request, *args, **kwargs):
        request.data['customer'] = request.user.customer.id
        request.data['last_updated_by'] = request.user.username
        partial = kwargs.pop('partial', False)
        id = request.data.get('id')
        if not id:
            return Response({"message":"Please pass id to update User", "status":400}) 
        instance = self.get_queryset({"id":id}).first()        
        if not instance:
            return JsonResponse({"message":"No Record found", "status":400}) 
        role_name = request.data.get('role_name')
        role_id = self.get_role_id(role_name)
        if role_id is None:
            return Response({"error": "Role with the provided name does not exist"})
        request.data['role'] = role_id
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "User updated successfully", "data": serializer.data, "status": 200})

    def delete(self, request, *args, **kwargs):
        id = request.GET.get('id')
        if not id:
            return Response({"message":"Please pass id to delete User", "status":400}) 
        instance = self.get_queryset({"id":id}).first()
        if not instance:
            return JsonResponse({"message":"No Record found", "status":400})
        instance.is_active = False
        instance.status = False
        instance.last_updated_by = self.request.user.username
        instance.save()
        return Response({"message":"User deleted Succesfully", "status":200})


class CustomerOrEnterpriseView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend, rest_filters.OrderingFilter)
    filterset_class = CustomerFilter
    serializer_class = CustomerSerializer

    ordering_fields = ['id', 'created_at', 'last_updated_at'] #for ordering or sorting replace with '__all__' for all fields
    ordering = [] # for default orderings

    def get_queryset(self, filters={}):
        return Customer.objects.filter(**filters)

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse({'data': serializer.data}, safe=False)

    def post(self, request, *args, **kwargs):
        request.data['last_updated_by'] = request.user.username
        request.data['created_by'] = request.user.username
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer_instance = serializer.save()
        user_serializer = UserSerializer(data={"username": customer_instance.name, "password": customer_instance.name, "first_name": customer_instance.name, "last_name": customer_instance.name, "email": customer_instance.name+"@gmail.com", "is_active": 1, "is_staff": 1, "status": 1, "valid_till": customer_instance.valid_till, "customer": customer_instance.id, "last_updated_by": customer_instance.name, "role_name": "ADMIN", "role": 2})
        if user_serializer.is_valid():
            user_serializer.save()
            return JsonResponse({"message": "Customer and User created successfully", "customer_data": serializer.data, "user_data": user_serializer.data, "status": 200})
        else:
            customer_instance.delete()  # Rollback customer creation if user creation fails
            return JsonResponse({"error": "Failed to create Customer and User", "customer_data": serializer.data, "user_errors": user_serializer.errors, "status": 400})
        
    def put(self, request, *args, **kwargs):
        request.data['last_updated_by'] = request.user.username
        partial = kwargs.pop('partial', False)
        id = request.data.get('id')
        if not id:
            return JsonResponse({"message":"Please pass id to update Customer", "status":400}) 
        instance = self.get_queryset({"id":id}).first()        
        if not instance:
            return JsonResponse({"message":"No Record found", "status":400}) 
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse({"message": "Customer updated successfully", "data": serializer.data, "status": 200})

    def delete(self, request, *args, **kwargs):
        id = request.GET.get('id')
        if not id:
            return JsonResponse({"message":"Please pass id to delete Customer", "status":400}) 
        instance = self.get_queryset({"id":id}).first()
        if not instance:
            return JsonResponse({"message":"No Record found", "status":400})
        instance.status = False
        instance.last_updated_by = self.request.user.username
        instance.save()
        return JsonResponse({"message":"Customer deleted Succesfully", "status":200})


class CheckUsernameExistsView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend, rest_filters.OrderingFilter)

    def get(self, request, *args, **kwargs):
        username = request.GET.get('username', None)
        return Response({"does_exist": User.all_objects.filter(username = username).exists()})
    

class CheckEmailExistsView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend, rest_filters.OrderingFilter)

    def get(self, request, *args, **kwargs):
        email = request.GET.get('email', None)
        return Response({"does_exist": User.all_objects.filter(email = email).exists()})

    
class CreateRoleWithGroupsAPIView(generics.CreateAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)

    def post(self, request, *args, **kwargs):
            role_name = request.data.get('role_name')
            group_names = request.data.get('group_names', [])
            role, created = Role.objects.get_or_create(name=role_name)
            groups = Group.objects.filter(name__in=group_names)
            role.groups.add(group)
            role.save()
            return Response({"message": "Groups assigned to role successfully"})


class InsertGitView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend, rest_filters.OrderingFilter)
    filterset_class = CustomerFilter
    serializer_class = CustomerSerializer

    ordering_fields = ['id', 'created_at', 'last_updated_at'] #for ordering or sorting replace with '__all__' for all fields
    ordering = [] # for default orderings