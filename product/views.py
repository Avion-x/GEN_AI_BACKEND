from product.filters import TestTypeFilter, ProductCategoryFilter
from rest_framework import generics, viewsets, filters as rest_filters
from django_filters import rest_framework as django_filters
from rest_framework.response import Response
import git
import os
from django.conf import settings

from .models import TestType, ProductCategory, ProductSubCategory, Product
from .serializers import TestTypeSerializer, ProductCategorySerializer, ProductSubCategorySerializer, ProductSerializer
from .filters import TestTypeFilter, ProductCategoryFilter, ProductSubCategoryFilter, ProductFilter
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse, JsonResponse
import json
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import BasicAuthentication, TokenAuthentication



# Create your views here.
class TestTypeView(generics.ListAPIView):
    
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)
    filterset_class = TestTypeFilter
    ordering_fields = ['id', 'created_at', 'last_updated_at']
    ordering = [] # for default orderings

    def get_queryset(self):
        return TestType.objects.filter()

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        print(queryset.query)
        serializer = TestTypeSerializer(queryset, many=True)
        return JsonResponse({'data':serializer.data}, safe=False)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse(serializer.data, status=201)

    def put(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse(serializer.data)

class ProductCategoryView(generics.ListAPIView):

    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)
    filterset_class = ProductCategoryFilter
    ordering_fields = ['id', 'created_at', 'last_updated_at']
    ordering = [] # for default orderings

    def get_queryset(self):
        return ProductCategory.objects.filter()

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        print(queryset.query)
        serializer = ProductCategorySerializer(queryset, many=True)
        return JsonResponse({'data':serializer.data}, safe=False)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse(serializer.data, status=201)

    def put(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse(serializer.data)

class ProductSubCategoryView(generics.ListAPIView):

    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)
    filterset_class = ProductSubCategoryFilter
    ordering_fields = ['id', 'created_at', 'last_updated_at']
    ordering = [] # for default orderings

    def get_queryset(self):
        return ProductSubCategory.objects.filter()

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        print(queryset.query)
        serializer = ProductSubCategorySerializer(queryset, many=True)
        return JsonResponse({'data':serializer.data}, safe=False)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse(serializer.data, status=201)

    def put(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse(serializer.data)
    
class ProductView(generics.ListAPIView):

    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)
    filterset_class = ProductFilter
    ordering_fields = ['id', 'created_at', 'last_updated_at']
    ordering = [] # for default orderings

    def get_queryset(self):
        return Product.objects.filter()

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        print(queryset.query)
        serializer = ProductSerializer(queryset, many=True)
        return JsonResponse({'data':serializer.data}, safe=False)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse(serializer.data, status=201)

    def put(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse(serializer.data)

class FileUploadView(generics.ListAPIView):

    def post(self, request, *args, **kwargs):
        if 'file' in request.FILES:
            uploaded_file = request.FILES['file']
            try:
                # Save the file to the server
                file_path = os.path.join(settings.BASE_DIR, 'uploads', uploaded_file.name)
                with open(file_path, 'wb+') as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)

                # Commit and push changes to GitHub using GitPython
                repo_path = os.path.join(settings.BASE_DIR, 'Avion-x/AI_GEN_TEST_CASES')
                repo = git.Repo(repo_path)
                repo.git.add('.')
                repo.git.commit('-m', f'Add uploaded file: {uploaded_file.name}')
                repo.git.push()

            except Exception as e:
                return JsonResponse(f'Error updating GitHub: {e}', safe= False)

            return JsonResponse('File uploaded', safe= False)

        return JsonResponse('No File', safe= False)
