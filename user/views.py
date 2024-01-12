from rest_framework import generics, viewsets, filters as rest_filters
from django_filters import rest_framework as django_filters
from rest_framework.response import Response

from user.filters import CustomUserFilter
from .models import User, Customer, CustomerConfig, AccessType
from product.models import TestType
from .serializers import UserRetriveSerializer, UserSerializer, CustomerSerializer, CustomerConfigSerializer, TestTypeSerializer, AccessTypeSerializer
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
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
            token, created = Token.objects.get_or_create(user=request.user)
            return Response({'token': token.key})
            serializer = UserRetriveSerializer(user)
            return Response(serializer.data)
        else:
            # Authentication failed
            return Response({'error': 'Invalid credentials'})


class LogoutView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        logout(request)
        return redirect('login')

class UserView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend, rest_filters.OrderingFilter)
    filterset_class = CustomUserFilter
    serializer_class = UserSerializer

    ordering_fields = ['id', 'date_joined', 'last_login'] #for ordering or sorting replace with '__all__' for all fields 
    ordering = [] # for default orderings

    def get_queryset(self):
        return User.objects.filter()

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = UserRetriveSerializer(queryset, many=True)
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


