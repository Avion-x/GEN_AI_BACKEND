from datetime import date
from product.services.aws_bedrock import AwsBedrock
from user.models import CustomerConfig
from product.services.custom_logger import logger
from product.services.github_service import push_to_github
from product.services.generic_services import get_prompts_for_device, get_string_from_datetime, validate_mandatory_checks
from product.filters import TestTypeFilter, ProductCategoryFilter
from rest_framework import generics, viewsets, filters as rest_filters
from django_filters import rest_framework as django_filters
from rest_framework.response import Response
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
from product.services.open_ai import CustomOpenAI


# Create your views here.
class TestTypeView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)
    filterset_class = TestTypeFilter
    ordering_fields = ['id', 'created_at', 'last_updated_at']
    ordering = [] # for default orderings

    def get_queryset(self):
        try:
            return TestType.objects.filter()
        except Exception as e:
            logger.error(level='ERROR', message = "")

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
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
                    "convert_type" : True,
                    "convert_expression" : str
                },
                "ai_model" : {
                    "is_mandatory" : False,
                    "type":str,
                    "convert_type" : False,
                },

            }
    AiModels = {
        "open_ai" : CustomOpenAI,
        "anthropic.claude-v2:1" : AwsBedrock,
        "anthropic.claude-v2" : AwsBedrock,
        'amazon.titan-text-express-v1': AwsBedrock,
    }

    def set_device(self, device_id):
        try:
            self.device = Product.objects.get(id=device_id, customer = self.request.user.customer, status=True, valid_till__gte = date.today())
        except Exception as e:
            raise e
        
    def get_ai_obj(self,data):
        try:
            model = data.get('ai_model', "open_ai")
            ai_model = self.AiModels.get(model, None)
            if not ai_model:
                raise Exception(f"Please provide valid ai_model, Available models are {list(self.AiModels.keys())}")
            return ai_model(modelId=model)
        except Exception as e:
            raise e
        
    def post(self, request):
        try:
            response = {}
            data = validate_mandatory_checks(input_data=request.data, checks=self.validation_checks)
            self.ai_obj = self.get_ai_obj(data)
            self.set_device(data['device_id'])
            prompts_data = get_prompts_for_device(**data)
            for test, test_data in prompts_data.items(): 
                print(test, test_data)
                response[test] = self.execute(request, test, test_data)

            return Response( {
                "error": "",
                "status": 200,
                "response" : response
            })
        
        except Exception as e:
            return Response({
                "error" : f"{e}",
                "status" : 400,
                "response" : {}
            })
        
    def execute(self, request, test_type, input_data):
        try:
            response = {}
            insert_data = {"test_type_id":input_data.pop("test_type_id",None), "device_id":self.device.id, "prompts":input_data}
            for test_code, propmts in input_data.items():
                file_path = self.get_file_path(request, test_type, test_code)
                response[test_code] = self.generate_tests(prompts=propmts)
                insert_data['git_data'] = push_to_github(data=response[test_code], file_path=file_path)
                insert_test_case(request, data = insert_data.copy())
            return response
        except Exception as e:
            raise e
        
    def get_file_path(self, request, test_type, test_code):
        try:
            device_code = self.device.product_code
            path = CustomerConfig.objects.filter(config_type = 'repo_folder_path', customer=request.user.customer).first().config_value
            return path.replace("${device_code}", device_code) \
                           .replace("${test_type}", test_type) \
                           .replace("${test_code}", test_code)
        except Exception as e:
            return f"data/{request.user.customer.code}/{test_type}/{test_code}"
    
    def generate_tests(self, prompts, **kwargs):
        try:
            response_data = ""
            for prompt in prompts:
                kwargs['prompt']=prompt
                prompt_data = self.ai_obj.send_prompt(**kwargs)
                response_data += prompt_data
            return response_data
        except Exception as e:
            raise e
        

def insert_test_case(request, data):
    try:
        record = {
            "customer" : request.user.customer,
            "product_id":data.pop("device_id"),
            "created_by": request.user,
            "data_url": data.get('git_data').get("url"),
            "sha": data.get('git_data').get("sha"),
            "test_type_id": data.pop("test_type_id"),
            "data": data,

        }
        return TestCases.objects.create(**record)
    except Exception as e:
        raise Exception(e)



