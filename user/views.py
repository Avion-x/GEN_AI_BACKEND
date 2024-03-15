from rest_framework import generics, viewsets,permissions, authentication, filters as rest_filters, status
from django_filters import rest_framework as django_filters
from rest_framework.response import Response
from django.db import IntegrityError
from django.contrib.auth.models import Group, Permission
from user.filters import CustomUserFilter
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

    def get_queryset(self):
        return User.objects.filter()

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset().order_by('first_name'))
        serializer = UserRetriveSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        request.data['customer']=request.user.customer.id
        request.data['last_updated_by']=request.user.id
        role_name = request.data.get('role_name')
        role_id = self.get_role_id(role_name)
        if role_id is None:
            return Response({"error": "Role with the provided name does not exist"})
        request.data['role'] = role_id
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "User created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)

    def put(self, request, *args, **kwargs):
        request.data['customer']=request.user.customer.id
        request.data['last_updated_by']=request.user.id
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        role_name = request.data.get('role_name')
        role_id = self.get_role_id(role_name)
        if role_id is None:
            return Response({"error": "Role with the provided name does not exist"})
        request.data['role'] = role_id
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "User updated successfully", "data": serializer.data})

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(status=204)


class CustomerOrEnterpriseView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend, rest_filters.OrderingFilter)
    serializer_class = CustomerSerializer

    ordering_fields = ['id', 'created_at', 'last_updated_at'] #for ordering or sorting replace with '__all__' for all fields
    ordering = [] # for default orderings

    def get_queryset(self):
        return Customer.objects.filter()

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)

    def put(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(status=204)


class CheckUsernameExistsView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend, rest_filters.OrderingFilter)

    def get(self, request, *args, **kwargs):
        username = request.GET.get('username', None)
        return Response({"does_exist": User.all_objects.filter(username = username).exists()})

    
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