from product.services.custom_logger import logger
from product.services.github_service import push_to_github
from product.services.generic_services import get_prompts_for_device, get_string_from_datetime, validate_mandatory_checks
from product.filters import TestTypeFilter, ProductCategoryFilter
from rest_framework import generics, viewsets, filters as rest_filters
from django_filters import rest_framework as django_filters
from rest_framework.response import Response
# import git
import os
from django.conf import settings

from .models import TestCases, TestType, ProductCategory, ProductSubCategory, Product
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

from product.services.open_ai import send_prompt


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
        return ProductCategory.objects.filter(customer_id = self.request.user.customer_id)

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        print(queryset.query)
        serializer = ProductCategorySerializer(queryset, many=True)
        # return JsonResponse({'data':serializer.data}, safe=False)
        return Response(serializer.data)

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
        return ProductSubCategory.objects.filter(customer_id = self.request.user.customer_id)

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = ProductSubCategorySerializer(queryset, many=True)
        logger.log(level="INFO", message="Product Sub Categories api")
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
        return Product.objects.filter(customer_id = self.request.user.customer_id)

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

class GenerateTestCases(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    validation_checks = {
                "device_id" : {
                    "is_mandatory" : True,
                    "type" : str,
                    "convert_type" : True,
                },
                "test_type_id" : {
                    "is_mandatory" : True,
                    "type" : list,
                    "convert_type" : True
                },

            }
    
    def post(self, request):
        try:
            data = validate_mandatory_checks(input_data=request.data, checks=self.validation_checks)
            data['prompts'] = get_prompts_for_device(**data)
            file_name = get_string_from_datetime() + ".md"
            response_data = self.generate_tests(prompts=data['prompts'], file_name = file_name)
            data['new_file_url'] = push_to_github(data=response_data,file_path=f'data/{file_name}')
            insert_test_case(request, data = data)

            return Response( {
                "error": "",
                "status": 200,
                "response" : response_data
            })
        
        except Exception as e:
            return Response({
                "error" : f"{e}",
                "status" : 400,
                "response" : {}
            })
    
    def generate_tests(self, prompts, file_name):
        try:
            response_data = ""
            for prompt in prompts:
                prompt_data = send_prompt(prompt, output_file=file_name)
                response_data += prompt_data
                break
            return response_data
        except Exception as e:
            raise e
        

def insert_test_case(request, data):
    try:
        data['test_types'] = list(TestType.objects.filter(id__in=data.pop("test_type_id")).values('id', 'code'))
        record = {
            "customer" : request.user.customer,
            "product_id":data.pop("device_id"),
            "created_by": request.user,
            "data_url": data.pop("new_file_url"),
            "data": data

        }
        return TestCases.objects.create(**record)
    except Exception as e:
        raise Exception(e)



