import asyncio
from collections import defaultdict
from datetime import date, datetime, timedelta
import io
import threading
import time

import numpy as np
import pandas as pd
from product.services.dynamic_paramters_fetch import TestSubCategoryParameters
from product.paginator import CustomPagination
from product.services.aws_bedrock import AwsBedrock
from user.models import CustomerConfig, User
from product.services.custom_logger import logger
from product.services.github_service import CustomGithub, push_to_github, get_commits_for_file, get_changes_in_file, \
    get_files_in_commit
from product.services.generic_services import DevicePrompts, get_prompts_for_device, get_string_from_datetime, parseModelDataToList, read_csv_from_s3, test_response, \
    validate_mandatory_checks
from product.services.juniper_config_parser import process_network_config
from product.filters import TestTypeFilter, ProductCategoryFilter
from rest_framework import generics, viewsets, filters as rest_filters
from django_filters import rest_framework as django_filters
from rest_framework.response import Response
from .models import Paramters, RuntimeParameterValues, StructuredTestCases, TestCases, TestType, ProductCategory, ProductSubCategory, Product, \
    TestScriptExecResults, UserCreatedTestCases, TestSubCategories, Customer
from .serializers import GenereateTestCaseJobDataSerializer, TestSubCategoryParamtersSerializer, TestTypeSerializer, ProductCategorySerializer, ProductSubCategorySerializer, ProductSerializer, UserCreatedTestCasesSerializer
from .filters import TestTypeFilter, ProductCategoryFilter, ProductSubCategoryFilter, ProductFilter, \
    LatestTestTypesWithCategoriesOfProductFilter, TestSubCategoriesFilter
# import git
import os
from django.db.models import F, Q, Value, Count, Max, Min, JSONField, BooleanField, ExpressionWrapper, CharField, Case, \
    When, Sum, CharField, IntegerField
from django.db.models.functions import Cast

from .models import TestCases, TestType, ProductCategory, ProductSubCategory, Product, TestCategories, DocumentUploads, Paramters
from .serializers import TestTypeSerializer, ProductCategorySerializer, ProductSubCategorySerializer, ProductSerializer, \
    TestCasesSerializer, TestCategoriesSerializer, TestScriptExecResultsSerializer, TestSubCategoriesSerializer
from .filters import TestTypeFilter, ProductCategoryFilter, ProductSubCategoryFilter, ProductFilter, TestCasesFilter, \
    TestCategoriesFilter, TestExecutionResultsFilter
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
import json
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from product.services.open_ai import CustomOpenAI
from product.services.langchain_ import Langchain_
import pdfplumber, boto3
from io import BytesIO, StringIO
from product.services.generic_services import extract_pdf
from event_manager.models import CronExecution
from event_manager.service.cronjob import CronJob

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from botocore.exceptions import ClientError
from boto3.s3.transfer import S3Transfer
from sentence_transformers import SentenceTransformer, util

from constants import OPEN_API_REGISTRY, GITHUB_API_REGISTRY

import boto3
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_REGION = os.environ.get('AWS_DEFAULT_REGION')

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION  # Override default region
)
s3 = session.client('s3')


# Create your views here.
class TestTypeView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)
    filterset_class = TestTypeFilter
    serializer_class = TestTypeSerializer
    ordering_fields = ['id', 'created_at', 'last_updated_at']
    ordering = []  # for default orderings
    ALLOWED_TYPES = ['TESTTYPE', 'TOPOLOGY', 'USECASE']

    def get_queryset(self, filters={}):
        try:
            return TestType.objects.filter(**filters)
        except Exception as e:
            logger.log(level='ERROR', message=f"Error retriving Test Type queryset: {e}")

    def get(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = TestTypeSerializer(queryset, many=True)
            logger.log(level='INFO', message="Test Type data fetched successfully.")
            return JsonResponse({'data': serializer.data}, safe=False)
        except Exception as e:
            logger.log(level="ERROR", message=f"Error while retriving data: {e}")
            return JsonResponse({"data": "Something went wrong"})

    def post(self, request, *args, **kwargs):
        try:
            request.data['last_updated_by'] = self.request.user.username
            type_value = request.data.get('type')
            if not type_value:
                return JsonResponse({"message": "Please Enter a Test Type", "status": 400})
            if type_value not in self.ALLOWED_TYPES:
                return JsonResponse({"message": f"Invalid Input. Allowed options are {', '.join(self.ALLOWED_TYPES)}", "status": 400})
            
            product_ids = request.data.get('product_id', [])
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            test_type = serializer.save()

            for product_id in product_ids:
                try:
                    product = Product.objects.get(id=product_id)
                    test_type.product.add(product)
                    logger.log(level='INFO', message=f"Product with ID: {product_id} added to Test Type")
                except Product.DoesNotExist:
                    logger.log(level='ERROR', message=f"Product with id {product_id} does not exist.")
                    return JsonResponse({"message": f"Product with id {product_id} does not exist."})

            logger.log(level='INFO',message=f"Test Type created sucessfully.")
            return JsonResponse({"message": "Test Type created successfully", "data": serializer.data, "status": 200})
        except Exception as e:
            logger.log(level="ERROR",message=f"Error while creating Test Type,{e}")
            return JsonResponse({"data": "Something went wrong"})

    def put(self, request, *args, **kwargs):
        try:
            request.data['last_updated_by'] = self.request.user.username
            partial = kwargs.pop('partial', False)
            id = request.data.get('id')
            if not id:
                return Response({"message": "Please pass id to update Test Type", "status": 400})
            instance = self.get_queryset({"id": id}).first()
            if not instance:
                return JsonResponse({"message": "No Record found", "status": 400})
            
            product_ids = request.data.get('product_ids', [])
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            test_type = serializer.save()

            for product_id in product_ids:
                try:
                    product = Product.objects.get(id=product_id)
                    test_type.product.add(product)
                    logger.log(level='INFO', message=f"Product with ID: {product_id} added to Test Type")
                except Product.DoesNotExist:
                    logger.log(level='ERROR', message=f"Product with id {product_id} does not exist.")
                    return JsonResponse({"message": "Test Type updated successfully", "data": serializer.data, "status": 200})
                    
            logger.log(level='INFO',message=f"Test Type updated sucessfully.")
            return JsonResponse({"message": "Test Type updated successfully", "data": serializer.data, "status": 200})
        except Exception as e:
            logger.log(level="ERROR", message=f"Error while updating Test Type,{e}")
            return JsonResponse({"data": "Something went wrong"})

    def delete(self, request, *args, **kwargs):
        try:
            id = request.GET.get('id')
            if not id:
                return Response({"message": "Please pass id to delete Test Type", "status": 400})
            instance = self.get_queryset({"id": id}).first()
            if not instance:
                return JsonResponse({"message": "No Record found", "status": 400})
            test_categories_count = TestType.objects.get(id=id).test_category.count()
            if test_categories_count != 0:
                return JsonResponse(
                    {"message": "Cannot delete this Test Type as it contains Test Categories", "status": 400})
            instance.status = 0
            instance.last_updated_by = self.request.user.username
            instance.save()
            logger.log(level='INFO', message="Test Type deleted successfully.")
            return JsonResponse({"message": "Test Type deleted successfully", "status": 200})
        except Exception as e:
            logger.log(level="ERROR", message=f"Error while deleting Test Type,{e}")
            return JsonResponse({"data": "Something went wrong"})

class ProductCategoryView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)
    filterset_class = ProductCategoryFilter
    serializer_class = ProductCategorySerializer
    ordering_fields = ['id', 'created_at', 'last_updated_at']
    ordering = []  # for default orderings

    def get_queryset(self, filters={}):
        try:
            return ProductCategory.objects.filter(**filters)
        except Exception as e:
            logger.log(level='ERROR', message=f"Error retriving Category queryset: {e}")

    def get(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = ProductCategorySerializer(queryset, many=True)
            # return JsonResponse({'data':serializer.data}, safe=False)
            logger.log(level='INFO', message="Category data fetched successfully.")
            return Response(serializer.data)
        except Exception as e:
            logger.log(level="ERROR", message=f"Error while retriving data: {e}")
            return JsonResponse({"data": "Something went wrong"})

    def post(self, request, *args, **kwargs):
        try:
            request.data['customer'] = self.request.user.customer_id
            request.data['last_updated_by'] = self.request.user.id
            request.data['created_by'] = self.request.user.id
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            logger.log(level='INFO',message=f"Category created sucessfully.")
            return JsonResponse({"message": "Category created successfully", "data": serializer.data, "status": 200})
        except Exception as e:
            logger.log(level="ERROR",message=f"Error while creating Category,{e}")
            return JsonResponse({"data": "Something went wrong"}) 

    def put(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            id = request.data.get('id')
            if not id:
                return Response({"message": "Please pass id to update Category", "status": 400})
            instance = self.get_queryset({"id": id}).first()
            if not instance:
                return JsonResponse({"message": "No Record found", "status": 400})
            request.data['customer'] = self.request.user.customer_id
            request.data['last_updated_by'] = self.request.user.id
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            logger.log(level='INFO',message=f"Category updated sucessfully.")
            return JsonResponse({"message": "Category updated successfully", "data": serializer.data, "status": 200})
        except Exception as e:
            logger.log(level="ERROR", message=f"Error while updating Category,{e}")
            return JsonResponse({"data": "Something went wrong"})

    def delete(self, request, *args, **kwargs):
        try:
            id = request.GET.get('id')
            if not id:
                return Response({"message": "Please pass id to delete Category", "status": 400})
            instance = self.get_queryset({"id": id}).first()
            if not instance:
                return JsonResponse({"message": "No Record found", "status": 400})
            sub_categories_count = ProductCategory.objects.get(id=id).product_sub_category.count()
            if sub_categories_count != 0:
                return JsonResponse({"message": "Cannot delete this Category as it contains Sub Categories", "status": 400})
            instance.status = 0
            instance.last_updated_by = self.request.user
            instance.save()
            logger.log(level='INFO', message="Category deleted successfully.")
            return JsonResponse({"message": "Category deleted successfully", "status": 200})
        except Exception as e:
            logger.log(level="ERROR", message=f"Error while deleting Category,{e}")
            return JsonResponse({"data": "Something went wrong"})


class ProductSubCategoryView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)
    filterset_class = ProductSubCategoryFilter
    serializer_class = ProductSubCategorySerializer
    ordering_fields = ['id', 'created_at', 'last_updated_at']
    ordering = []  # for default orderings

    def get_queryset(self, filters={}):
        try:
            return ProductSubCategory.objects.filter(**filters)
        except Exception as e:
            logger.log(level='ERROR', message=f"Error retriving Sub Category queryset: {e}")      

    def get(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = ProductSubCategorySerializer(queryset, many=True)
            logger.log(level="INFO", message="Sub Category data fetched successfully.")
            return JsonResponse({'data': serializer.data}, safe=False)
        except Exception as e:
            logger.log(level="ERROR", message=f"Error while retriving data: {e}")
            return JsonResponse({"data": "Something went wrong"})

    def post(self, request, *args, **kwargs):
        try:
            request.data['customer'] = self.request.user.customer_id
            request.data['last_updated_by'] = self.request.user.id
            request.data['created_by'] = self.request.user.id
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            logger.log(level='INFO',message=f"Sub Category created sucessfully.")
            return JsonResponse({"message": "Sub Category created successfully", "data": serializer.data, "status": 200})
        except Exception as e:
            logger.log(level="ERROR",message=f"Error while creating Sub Category,{e}")
            return JsonResponse({"data": "Something went wrong"})

    def put(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            id = request.data.get('id')
            if not id:
                return Response({"message": "Please pass id to update Sub Category", "status": 400})
            instance = self.get_queryset({"id": id}).first()
            if not instance:
                return JsonResponse({"message": "No Record found", "status": 400})
            request.data['customer'] = self.request.user.customer_id
            request.data['last_updated_by'] = self.request.user.id
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            logger.log(level='INFO',message=f"Sub Category updated sucessfully.")
            return JsonResponse({"message": "Sub Category updated successfully", "data": serializer.data, "status": 200})
        except Exception as e:
            logger.log(level="ERROR", message=f"Error while updating Sub Category,{e}")
            return JsonResponse({"data": "Something went wrong"})

    def delete(self, request, *args, **kwargs):
        try:
            id = request.GET.get('id')
            if not id:
                return Response({"message": "Please pass id to delete Sub Category", "status": 400})
            instance = self.get_queryset({"id": id}).first()
            if not instance:
                return JsonResponse({"message": "No Record found", "status": 400})
            product_count = ProductSubCategory.objects.get(id=id).product.count()
            if product_count != 0:
                return JsonResponse({"message": "Cannot delete this Sub Category as it contains Devices", "status": 400})
            instance.status = 0
            instance.last_updated_by = self.request.user
            instance.save()
            logger.log(level='INFO', message="Sub Category deleted successfully.")
            return JsonResponse({"message": "Sub Category deleted successfully", "status": 200})
        except Exception as e:
            logger.log(level="ERROR", message=f"Error while deleting Sub Category,{e}")
            return JsonResponse({"data": "Something went wrong"})


class ProductView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)
    filterset_class = ProductFilter
    serializer_class = ProductSerializer
    ordering_fields = ['id', 'created_at', 'last_updated_at']
    ordering = []  # for default orderings

    def get_queryset(self, filters={}):
        try:
            return Product.objects.filter(**filters)
        except Exception as e:
            logger.log(level='ERROR', message=f"Error retriving Product queryset: {e}")

    def get(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = ProductSerializer(queryset, many=True)
            non_empty = []
            data = serializer.data
            if request.GET.get('test_types_available', False):
                for key in data:
                    if len(key['test_types']) != 0:
                        non_empty.append(key)
                data = non_empty
            logger.log(level="INFO", message="Product data fetched successfully.")
            return JsonResponse({'data': data}, safe=False)
        except Exception as e:
            logger.log(level="ERROR", message=f"Error while retriving data: {e}")
            return JsonResponse({"data": "Something went wrong"})

    def post(self, request, *args, **kwargs):
        try:
            request.data['customer'] = self.request.user.customer_id
            request.data['last_updated_by'] = self.request.user.id
            request.data['created_by'] = self.request.user.id
            test_type_ids = request.data.get('test_type_id', [])
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            product = serializer.save()

            for test_type_id in test_type_ids:
                try:
                    test_type = TestType.objects.get(id=test_type_id)
                    product.test_type.add(test_type)
                    logger.log(level='INFO', message=f"Test Type with ID: {test_type_id} added to Test Type")
                except TestType.DoesNotExist:
                    logger.log(level='ERROR', message=f"Test Type with id {test_type_id} does not exist.")
            logger.log(level='INFO',message=f"Product created sucessfully.")
            return JsonResponse({"message": "Product created successfully", "data": serializer.data, "status": 200})
        except Exception as e:
            logger.log(level="ERROR",message=f"Error while creating Product,{e}")
            return JsonResponse({"data": "Something went wrong"})

    def put(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            id = request.data.get('id')
            if not id:
                return Response({"message": "Please pass id to update Product", "status": 400})
            instance = self.get_queryset({"id": id}).first()
            if not instance:
                return JsonResponse({"message": "No Record found", "status": 400})
            request.data['customer'] = self.request.user.customer_id
            request.data['last_updated_by'] = self.request.user.id
            test_type_ids = request.data.get('test_type_id', [])
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            product = serializer.save()

            for test_type_id in test_type_ids:
                try:
                    test_type = TestType.objects.get(id=test_type_id)
                    product.test_type.add(test_type)
                    logger.log(level='INFO', message=f"Test Type with ID: {test_type_id} added to Test Type")
                except TestType.DoesNotExist:
                    logger.log(level='ERROR', message=f"Test Type with id {test_type_id} does not exist.")
            logger.log(level='INFO',message=f"Product updated sucessfully.")
            return JsonResponse({"message": "Product updated successfully", "data": serializer.data, "status": 200})
        except Exception as e:
            logger.log(level="ERROR", message=f"Error while updating Product,{e}")
            return JsonResponse({"data": "Something went wrong"})

    def delete(self, request, *args, **kwargs):
        try:
            id = request.GET.get('id')
            if not id:
                return Response({"message": "Please pass id to delete Product", "status": 400})
            instance = self.get_queryset({"id": id}).first()
            if not instance:
                return JsonResponse({"message": "No Record found", "status": 400})
            instance.status = 0
            instance.last_updated_by = self.request.user
            instance.save()
            logger.log(level='INFO', message="Product deleted successfully.")
            return JsonResponse({"message": "Product deleted successfully", "status": 200})
        except Exception as e:
            logger.log(level="ERROR", message=f"Error while deleting Product,{e}")
            return JsonResponse({"data": "Something went wrong"})


class GenerateTestCases(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    pagination_class = CustomPagination
    validation_checks = {
        "device_id": {
            "is_mandatory": True,
            "type": str,
            "convert_type": False,
        },
        "test_type_data": {
            "is_mandatory": True,
            "type": list,
            "convert_type": True,
            "convert_expression": str
        },
        "ai_model": {
            "is_mandatory": False,
            "type": str,
            "convert_type": False,
        },
    }

    def post(self, request):
        try:
            data = validate_mandatory_checks(input_data=request.data, checks=self.validation_checks)
            device_prompts = DevicePrompts(request = request, **data)
            prompts_data = device_prompts.get_prompts()
            # prompts_data = get_prompts_for_device(**data)
            print(prompts_data)
            test_names = list(StructuredTestCases.objects.filter(type='TESTCASE').values_list('test_name', flat = True))
            git = CustomGithub(request.user.customer)
            git_config = git.get_git_cofig(request.user.customer)

            job_data = {
                "body" : data,
                "prompts_data" : prompts_data,
                "test_names" : test_names,
                "request_id" : request.request_id
            }

            CronExecution.objects.create(
                name="GENERATE_TEST_CASES",
                customer=request.user.customer,
                created_by=request.user,
                params=job_data,
                request_id=request.request_id
            )

            a = CronJob()
            thread = threading.Thread(target=a.performOperation, args=())
            thread.start()
            # self.process_request(request, prompts_data)

            response = {
                "request_id": request.request_id,
                "Message": "Processing request will take some time Please come here in 5 mins",
                "git_details": f"Pushing into branch - {git_config['branch']} of Repository - {git_config['repository']}"
            }
            logger.log(level='INFO', message="Generated test cases successfully.")
            return Response({
                "error": "",
                "status": 200,
                "response": response
            })

        except Exception as e:
            request.request_tracking.status_code = 400
            request.request_tracking.error_message = str(e)
            request.request_tracking.save()
            logger.log(level="ERROR", message=f"Error while generating test cases ,{e}")
            return Response({
                "error": f"{e}",
                "status": 400,
                "response": {}
            })
        
    def get(self, request):
        try:
            filters = self.get_filters(request)
            print(filters)
            jobs = CronExecution.objects.filter(name="GENERATE_TEST_CASES", **filters).order_by('-id')
            page = self.paginate_queryset(jobs)
            if page is not None:
                serializer = GenereateTestCaseJobDataSerializer(page, many=True, exclude_fields= [] if 'request_id' in filters else ['execution_result'])
            else:
                serializer = GenereateTestCaseJobDataSerializer(jobs, many=True, exclude_fields= [] if 'request_id' in filters else ['execution_result'])
            return self.get_paginated_response(data={
                "error": "",
                "status": 200,
                "data": serializer.data
            })
        except Exception as e:
            logger.log(level="ERROR", message=f"Error while getting generated test cases ,{e}")
            return Response({
                "error": f"{e}",
                "status": 400,
                "data": {}
            })

    def get_filters(self, request):
        filters = {}
        if request.GET.get('request_id', None):
            filters["request_id"] = request.GET.get('request_id')
        if request.GET.get('status', None):
            filters["execution_status"] = request.GET.get('status')
        if request.GET.get('is_admin', False):
            filters['created_by'] = request.user
        if request.GET.get('device_id', None):
            filters['params__body__device_id'] = request.GET.get('device_id')
        return filters


def insert_test_case(request, data):
    try:
        record = {
            "customer": request.user.customer,
            "product_id": data.pop("device_id"),
            "created_by": request.user,
            "data_url": data.get('git_data').get("url"),
            "sha": data.get('git_data').get("sha"),
            "test_category_id": data.pop("test_category_id"),
            "test_sub_category_id" : data.pop("test_sub_category_id"),
            "data": data,
            "request_id": request.request_id
        }
        return TestCases.objects.create(**record)
    except Exception as e:
        raise Exception(e)

class UserCreatedTestCasesAndScripts(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    validation_checks = {
        "testname": {
            "is_mandatory": True,
            "type": str,
            "convert_type": False,
        },
        "device_id": {
            "is_mandatory": True,
            "type": str,
            "convert_type": False,
            "convert_expression": str
        },
        "test_category_id": {
            "is_mandatory": True,
            "type": str,
            "convert_type": False,
        },
        "objective": {
            "is_mandatory": True,
            "type": str,
            "convert_type": False,
        },
        # "test_case_data": {
        #     "is_mandatory": True,
        #     "type": dict,
        #     "convert_type": False,
        # },
        "comment": {
            "is_mandatory": False,
            "type": dict,
            "convert_type": False,
        },
    }

    def post(self, request, *args, **kwargs):
        try:
            input_data = validate_mandatory_checks(input_data=request.data, checks=self.validation_checks)
            name = input_data.get('testname', input_data.get('name', "")).replace(" ", "_").lower()
            device = Product.objects.filter(id=input_data.get('device_id')).first()
            if not device:
                raise Exception("Please provide valid device_id")
            test_category = TestCategories.objects.filter(id= input_data.get('test_category_id')).first()
            if not test_category:
                raise Exception("Please provide valid test_category_id")
            self.device=device
            self.test_category = test_category
            self.test_id = f"{request.user.customer.name}_{test_category.test_type.name}_{test_category.name}_{device.product_code}_{name}".replace(" ", "_").lower()
            if UserCreatedTestCases.objects.filter(test_id=self.test_id).exists() or StructuredTestCases.objects.filter(test_id=self.test_id).exists():
                raise Exception("Test case already exists")
            
            test_case_file = request.FILES.get('test_case_file', None)
            test_case_file_data = test_case_file.read()
            test_case_file_data = test_case_file_data.decode('utf-8')

            test_script_file = request.FILES.get('script_file', None)
            test_script_file_data = test_script_file.read()
            test_script_file_data = test_script_file_data.decode('utf-8')
            file_path = self.get_file_path(request, test_category.test_type, test_category, test_code="CustomerCreated")

            self.push_to_git(data = [{"file_name": f"{file_path}/{test_case_file.name}", "content": test_case_file_data}, {"file_name": f"{file_path}/{test_script_file.name}", "content": test_script_file_data}])

            _test_case = {
                "test_id": self.test_id,
                "test_name" : f"{name}",
                "objective" : input_data.get("objective", ""),
                "data" : test_case_file_data,
                "type" : input_data.get("test_type", "TESTCASE").upper(),
                "test_category_id" : test_category.id,
                "product" : device,
                "customer" : request.user.customer,
                "request_id" : request.request_id,
                "created_by" : request.user,
                "comment" : input_data.get("comment", "user created").upper()
            }
            _test_script = {
                "test_id": self.test_id,
                "test_name" : f"{name}",
                "objective" : input_data.get("objective", ""),
                "data" : test_script_file_data,
                "type" : "TESTSCRIPT",
                "test_category_id" : test_category.id,
                "product" : device,
                "customer" : request.user.customer,
                "request_id" : request.request_id,
                "created_by" : request.user,
                "comment" : input_data.get("comment", "user created").upper()
            }
            UserCreatedTestCases.objects.create(**_test_case)
            UserCreatedTestCases.objects.create(**_test_script)
            return Response({"response" : {
                "message": "Test case created successfully",
                "test_id": self.test_id,
                "test_case_data" : test_case_file_data,
                "test_scripts_data" : test_script_file_data,
                "request_id": request.request_id
            }, "status": 200, "error": ""})
        except Exception as e:
            return Response({"error": f"{e}", "status": 400, "response": {}})
    
    def get_file_path(self, request, test_type, test_category, test_code):
        try:
            device_code = self.device.product_code
            path = CustomerConfig.objects.filter(config_type='repo_folder_path',
                                                 customer=request.user.customer).first().config_value
            return path.replace("${device_code}", device_code) \
                .replace("${test_type}", test_type) \
                .replace("${test_category}", test_category) \
                .replace("${test_code}", test_code)
        except Exception as e:
            return f"data/{request.user.customer.code}/{test_type}/{test_code}"
        
    def push_to_git(self, data):
        try:
            git = CustomGithub(self.request.user.customer)
            for item in data:
                file_name = item.get('file_name', None)
                content = item.get('content', "")
                git_response = git.push_to_github(data = content, file_path=file_name)
                data = ({"device_id": self.device.id, "test_category_id": self.test_category.id, "test_id": self.test_id, "git_data": git_response})
                insert_test_case(request=self.request, data=data)
        except Exception as e:
            raise e
        

    def get(self, request):
        try:
            filters = {}
            if request.GET.get('test_id'):
                filters['test_id'] = request.GET.get('test_id')
            
            if request.GET.get('test_category_id'):
                filters['test_category_id'] = request.GET.get('test_category_id')
            
            if request.GET.get('device_id'):
                filters['product_id'] = request.GET.get('device_id')

            if request.GET.get('test_type'):
                filters['type'] = request.GET.get('test_type').upper()
            
            if request.GET.get('request_id'):
                filters['request_id'] = request.GET.get('request_id')

            if request.GET.get('test_type_id'):
                filters['test_category__test_type_id'] = request.GET.get('test_type_id')
            
            queryset = UserCreatedTestCases.objects.filter(**filters)
            serializer = UserCreatedTestCasesSerializer(queryset, many=True)
            return Response({"data": serializer.data, "status": 200, "error": ""})
        except Exception as e:
            return Response({"error": f"{e}", "status": 400, "response": {}})


class TestCasesAndScripts(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)
    # filterset_class = TestCasesFilter
    ordering_fields = ['id', 'created_at', 'updated_at']

    def get_queryset(self, filters={}):
        try:
            data=StructuredTestCases.objects.filter(**filters)
            logger.log(level='INFO', message=f"retriving TestCasesAndScripts queryset:")
            return data
        except Exception as e:
            logger.log(level='ERROR', message=f"Error retriving TestCasesAndScripts queryset: {e}")
            return None

    def get(self, request, *args, **kwargs):
        try:
            test_type_id = request.GET.get("test_type_id", None)
            if not test_type_id:
                raise Exception("Please pass test_type_id to get test cases")
            filters = {
                "test_type_id": test_type_id,
            }
            product_id = request.GET.get("product_id", None)
            if product_id:
                filters['product_id'] = product_id
            test_category_id = request.GET.get("test_category_id", None)
            if not test_category_id:
                data = self.get_test_types_with_categories(filters)
            else:
                filters['test_category_id'] = test_category_id
                data = self.get_consolidated_data_of_test_category(self.get_queryset(filters))
                logger.log(level='INFO', message=f'sucessfully executed.')
            return Response({"data": data})
        except Exception as e:
            logger.log(level='ERROR', message=f'Failed to generate TestCaseAndscript executed.')
            return JsonResponse({'data': "Something went wrong"})

    def get_test_types_with_categories(self, filters):
        try:
            max_dates_subquery = self.get_queryset(filters).values('test_category_id').annotate(
                max_created_at=Max('created_at')).order_by("test_category")
            
            queryset = self.get_queryset(filters).filter(test_category_id__in=max_dates_subquery.values('test_category_id'),
                created_at__in=max_dates_subquery.values('max_created_at')).values("test_category_id").annotate(
                count=Count(F("test_category_id"))).values("test_category_id", "request_id", test_id=F("test_type_id"),
                test_name=F("test_type__code"), category_name=F("test_category__name")).order_by("test_type", "test_category")

            test_data = {}
            for item in list(queryset):
                test_id = item.pop('test_id')
                test_name = item.pop("test_name")
                try:
                    test_data[test_id]["categories"].append(item)
                except:
                    test_data[test_id] = {
                        "test_id": test_id,
                        "test_name": test_name,
                        "categories": [item]
                    }
                    logger.log(level='INFO', message=f'sucessfully executed.')
            return list(test_data.values())
        except Exception as e:
            logger.log(level='ERROR', message=f'Failed to generate TestCaseAndscript executed.')
            return JsonResponse({'data': "Something went wrong"})

    def get_consolidated_data_of_test_category(self, queryset):
        try:
            if not len(queryset):
                return {}

            # queryset = queryset.values('test_id').annotate(
            #     data=Case(
            #         When(type='TESTCASE', then=ExpressionWrapper(F('data'), output_field=JSONField())),
            #         When(type='TESTSCRIPT', then=Value({'TESTSCRIPT': F('data')}, output_field=JSONField())),
            #         default=Value({}, output_field=JSONField())
            #     )
            # )

            category_name = queryset.first().test_category.name

            test_cases = queryset.filter(type='TESTCASE').order_by('test_id').values('id', 'test_id', 'test_name',
                                                                                    'objective', 'data', 'status',
                                                                                    'valid_till', 'product_id',
                                                                                    product_name=F(
                                                                                        "product__product_code"),
                                                                                    user_id=F("created_by_id"),
                                                                                    user_name=F("created_by__username"))

            test_scripts = queryset.filter(type='TESTSCRIPT').order_by('test_id').values('id', 'test_id', 'test_name',
                                                                                        'objective', 'data', 'status',
                                                                                        'valid_till', 'product_id',
                                                                                        product_name=F(
                                                                                            "product__product_code"),
                                                                                        user_id=F("created_by_id"),
                                                                                        user_name=F(
                                                                                            "created_by__username"))

            serialized_data = {"test_cases": [], "test_scripts": [], "test_category": category_name}

            for test_case, test_script in zip(test_cases, test_scripts):
                _case = test_case['data']
                _script = test_script['data']
                for key in ['id', 'test_id', 'status', 'valid_till', 'product_id', 'product_name', 'user_id', 'user_name']:
                    _case[key] = test_case[key]
                    _script[key] = test_script[key]
                serialized_data['test_cases'].append(_case)
                serialized_data['test_scripts'].append(_script)
                logger.log(level='INFO', message=f'sucessfully executed.')
            return serialized_data
        except Exception as e:
            logger.log(level='ERROR', message=f'Failed to generate TestCaseAndscript executed.')
            return JsonResponse({'data': "Something went wrong"})
        


class GeneratedTestCategoriesView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)
    ordering_fields = []
    ordering = []

    def get(self, request, *args, **kwargs):
        try:
            test_type_id = request.GET.get('test_type_id', None)
            if not test_type_id:
                raise Exception("Please pass test_type_id")
            test_categories = TestCategories.objects.filter(test_type_id=test_type_id)
            categories = []
            for category in test_categories:
                result = {
                    "id": category.id,
                    "name": category.name
                }
                exists = StructuredTestCases.objects.filter(test_category_id=category.id).exists()
                result['is_generated'] = exists
                categories.append(result)
                logger.log(level='INFO', message=f" retriving GeneratedTestCategories queryset")
            return JsonResponse({'data': categories}, safe=False)
        except Exception as e:
            logger.log(level='Error', message=f"Error while retriving Generate test cases{e}")
            return JsonResponse({'data': "Something went wrong"})


class LatestTestTypesWithCategoriesOfProduct(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)
    filterset_class = LatestTestTypesWithCategoriesOfProductFilter
    ordering_fields = ['id', 'created_at', 'updated_at']

    def get_queryset(self, filters={}):
        return StructuredTestCases.objects.filter(**filters)

    def get(self, request, *args, **kwargs):
        try:
            product_id = request.GET.get("product_id", None)
            if not product_id:

                raise Exception("Please pass product_id to get test cases")
            filters = {
                "product_id": product_id,
            }
            queryset = self.get_queryset(filters=filters)
            latest_test_type_ids = queryset.annotate(latest=Max(F"test_type")).values_list(Max(F('id')), flat=True)

        except Exception as e:
            logger.log(level='Error', message=f"Error while retriving data. {e}")
            return JsonResponse({'data': "Something went wrong"})


class TestCasesView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)
    filterset_class = TestCasesFilter
    ordering_fields = ['id', 'created_at', 'updated_at']

    # ordering = []  # for default orderings

    def get_queryset(self):
        return TestCases.objects.filter()

    def get(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = TestCasesSerializer(queryset, many=True)
            logger.log(level='INFO',message=f'TestCase generated sucessfully.')
            return JsonResponse({'data': serializer.data}, safe=False)
        except Exception as e:
            logger.log(level='ERROR',message=f'failed to generate test cases.{e}')
            return JsonResponse({'data': "serialization failed"})

class GetFileCommitsView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)

    def get(self, request):
        try:
            file_path = request.query_params.get('file_path')
            repo = request.query_params.get('repo')
            response_data = get_commits_for_file(file_path=file_path, repo=repo)
            logger.log(level='INFO', message=f'TestCase generated sucessfully.')
            return JsonResponse(response_data, safe=False)
        except Exception as e:
            logger.log(level='ERROR', message=f'failed to generate test cases.{e}')
            return JsonResponse({'data': "Something went wrong"})


class GetFileChangesView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)

    def get(self, request):
        try:
            file_name = request.query_params.get('file_name')
            sha = request.query_params.get('sha')
            response_data = get_changes_in_file(file_name=file_name, commit_sha=sha)
            logger.log(level='INFO', message=f'TestCase generated sucessfully.')
            return JsonResponse({"data": response_data}, safe=False)
        except Exception as e:
            logger.log(level='ERROR', message=f'failed to generate test cases.{e}')
            return JsonResponse({'data': "Something went wrong"})


class GetFilesInCommitView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)

    def get(self, request):
        try:
            sha = request.query_params.get('sha')
            response_data = get_files_in_commit(sha)

            return JsonResponse(response_data, safe=False)
        except Exception as e:
            logger.log(level='ERROR', message=f'failed to generate test cases.{e}')
            return JsonResponse({'data': "Something went wrong"})


class TestCategoriesView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)
    filterset_class = TestCategoriesFilter
    serializer_class = TestCategoriesSerializer
    ordering_fields = ['id', 'created_at', 'last_updated_at']
    ordering = []  # for default orderings

    def get_queryset(self, filters={}):
        try:
            return TestCategories.objects.filter(**filters)
        except Exception as e:
            logger.log(level='ERROR', message=f"Error retriving TestCategories queryset: {e}")
            return None

    def get(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            logger.log(level='INFO', message=f'TestCategories generated sucessfully.')
            return JsonResponse({'data': serializer.data}, safe=False)
        except Exception as e:
            logger.log(level="ERROR", message=f"Error while retriving TestCategories,{e}")
            return JsonResponse({'error': f"Something went wrong: {e}"})

    def post(self, request, *args, **kwargs):
        try:
            request.data['customer'] = request.user.customer.id
            request.data['last_updated_by'] = request.user.id
            request.data['created_by'] = request.user.id
            request.data['is_approved'] = False
            request.data['approved_by'] = None
            data = request.data
            if data:
                test_type_name = TestType.objects.get(id=data['test_type']).code
                data['executable_codes'] = {"TestCases": {"code": f"{test_type_name} with category {data['name']}"},
                                            "TestScripts": {
                                                "code": f"python script in seperate file for each {test_type_name} for {data['name']}"}}
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            logger.log(level='INFO', message=f'TestCategories stored sucessfully.')
            return JsonResponse({"success": "Test Category Created successfully", "data": serializer.data, "status": 200})
        except Exception as e:
            logger.log(level="ERROR", message=f"Error while creating Test Caregorie,{e}")
            return JsonResponse({'error': f"Test Category Creation failed: {e}", "status": 400})

    def put(self, request, *args, **kwargs):
        try:
            request.data['customer'] = request.user.customer.id
            request.data['last_updated_by'] = request.user.id
            partial = kwargs.pop('partial', False)
            id = request.data.get('id')
            if not id:
                logger.log(level="ERROR", message=f"id not found in TestCategory.")
                return Response({"error": "Please pass id to update Test Category", "status": 400})
            instance = self.get_queryset({"id": id}).first()
            if not instance:
                logger.log(level="ERROR", message=f"instance not found in TestCategory.")
                return JsonResponse({"error": "No Record found", "status": 400})
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            logger.log(level='INFO', message=f'TestCategories updated sucessfully.')
            return JsonResponse({"success": "Test Category updated successfully", "data": serializer.data, "status": 200})
        except Exception as e:
            logger.log(level="ERROR", message=f"Error while Updating TestCategory,{e}")
            return JsonResponse({"error": f"Test Category update failed: {e}", "status": 400})

    def delete(self, request, *args, **kwargs):
        try:
            id = request.GET.get('id')
            if not id:
                logger.log(level="ERROR", message=f"Deletion failed in test Category")
                return JsonResponse({"error": "Please pass id to delete Test Category", "status": 400})
            instance = self.get_queryset({"id": id}).first()
            if not instance:
                logger.log(level="ERROR", message=f"Not a valid instance of Approve test Category")
                return JsonResponse({"error": "No Record found", "status": 400})
            instance.status = 0
            instance.last_updated_by = self.request.user
            instance.save()
            logger.log(level='INFO', message=f'TestCategories Deleted sucessfully.')
            return JsonResponse({"success": "Test Category deleted successfully", "status": 200})
        except Exception as e:
            logger.log(level="ERROR", message=f"Error while deleting Test Category,{e}")
            return JsonResponse({"error": f"Test Category deletion failed: {e}"})


class TestScriptExecResultsView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)
    filterset_class = TestExecutionResultsFilter
    ordering_fields = ['id', 'created_at']
    ordering = []

    def get_queryset(self):
        try:
            response= TestScriptExecResults.objects.filter(status=1,
                                                                test_script_number=self.request.data.get('test_script_number'))
            return response
        except Exception as e:
            logger.log(level="ERROR", message=f"Connectivity issues,{e}")
            return JsonResponse({'data': "Something went wrong"})

    def get(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = TestScriptExecResultsSerializer(queryset, many=True)
            logger.log(level='INFO', message=f'TestScriptExecResults fetched sucessfully.')
            return JsonResponse({'data': serializer.data}, safe=False)
        except Exception as e:
            logger.log(level="ERROR", message=f" Error while retriving TestScriptExecResults,{e}")
            return JsonResponse({'data': "TestScriptExecResults getting failed"})


class DashboardKpi(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)

    def get(self, request):
        try:
            total_devices = Product.objects.all().count()
            test_types = TestType.objects.all().count()
            users = User.objects.all().count()
            categories = ProductCategory.objects.all().count()
            sub_categories = ProductSubCategory.objects.all().count()
            devices_expire_in_30_days = Product.objects.filter(valid_till__gte=datetime.today(),
                                                            valid_till__lte=datetime.today() + timedelta(
                                                                days=30)).count()
            ready_to_test = StructuredTestCases.objects.filter().values('product_id').all().distinct().count()
            logger.log(level='INFO', message=f'Dashboard fetched sucessfully.')
            return Response({
                "status": 200,
                "data": [
                    {
                        "title": "Total Devices",
                        "value": total_devices,
                        "chart_data_point": "total_devices"
                    },
                    {
                        "title": "Test Types",
                        "value": test_types,
                        "chart_data_point": "test_types"
                    },
                    {
                        "title": "Users",
                        "value": users,
                        "chart_data_point": "users"
                    },
                    {
                        "title": "Categories",
                        "value": categories,
                        "chart_data_point": "categories"
                    },
                    {
                        "title": "Sub Categories",
                        "value": sub_categories,
                        "chart_data_point": "sub_categories"
                    },
                    {
                        "title": "Devices Expire In 30 Days",
                        "value": devices_expire_in_30_days,
                        "chart_data_point": "devices_expire_in_30_days"
                    },
                    {
                        "title": "Ready To Test",
                        "value": ready_to_test,
                        "chart_data_point": "ready_to_test"
                    },
                    # {
                    #     "title": "Test Scheduled Devices",
                    #     "value": 11,
                    #     "chart_data_point": 11
                    # }
                ]
            })
        except Exception as e:
            logger.log(level="ERROR", message=f"DashboardKpi getting failed,{e}")
            return JsonResponse({'data': "DashboardKpi getting failed"})


class PendingApprovalTestCategoryView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)
    filterset_class = TestCategoriesFilter
    serializer_class = TestCategoriesSerializer
    ordering_fields = ['id', 'created_at', 'last_updated_at']
    ordering = []  # for default orderings

    def get_queryset(self, filters={}):
        try:
            return TestCategories.objects.filter(**filters)
        except Exception as e:
            logger.log(level="ERROR", message=f"Connectivity issues,{e}")
            return JsonResponse({'data': "Something went wrong"})

    def get(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset({"is_approved": False}))
            serializer = self.get_serializer(queryset, many=True)
            return JsonResponse({'data': serializer.data}, safe=False)
        except Exception as e:
            logger.log(level="ERROR", message=f"PendingApprovalTestCategory getting failed,{e}")
            return JsonResponse({'data': "PendingApprovalTestCategory getting failed"})


class ApproveTestCategoryView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)
    filterset_class = TestCategoriesFilter
    serializer_class = TestCategoriesSerializer
    ordering_fields = ['id', 'created_at', 'last_updated_at']
    ordering = []  # for default orderings

    def get_queryset(self, filters={}):
        try:
            return TestCategories.objects.filter(**filters)
        except Exception as e:
            logger.log(level="ERROR", message=f"Connectivity issues,{e}")
            return JsonResponse({'error': f"Something went wrong: {e}"})

    def put(self, request, *args, **kwargs):
        try:
            if request.user.role_name == "USER":
                return Response({"error": "Test Category can approved only by an ADMIN", "status": 400})
            id = request.GET.get('id')
            if not id:
                logger.log(level="ERROR", message=f"Getting id failed in test Category")
                return Response({"error": "Please pass id to Approve Test Category", "status": 400})
            instance = self.get_queryset({"id": id}).first()
            if not instance:
                logger.log(level="ERROR", message=f"Not a valid instance of Approve test Category")
                return JsonResponse({"error": "No Record found", "status": 400})
            instance.is_approved = True
            instance.approved_by = self.request.user
            instance.save()
            logger.log(level='INFO', message=f'ApproveTestCategory updated sucessfully.')
            return JsonResponse({"success": "Test Category Approved successfully", "status": 200})
        except Exception as e:
            logger.log(level="ERROR", message=f"ApproveTestCategory update failed,{e}")
            return JsonResponse({'error': f"Test Category Approval failed: {e}"})


class DashboardChart(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)

    def get(self, request):
        try:
            registry = {
                "total_devices": Product.objects.all().values("id", "product_code", sub_category = F("product_sub_category__sub_category"), category=F("product_sub_category__product_category__category")),
                "test_types": TestType.objects.all().values("id", "name", "code", "description"),
                # "users": User.objects.aggregate(admins=Sum(Case(
                #     When(role_name="ADMIN", then=Value(1)),
                #     default=Value(0),
                #     output_field=IntegerField()
                # )), users=Sum(Case(
                #     When(role_name="USER", then=Value(1)),
                #     default=Value(0),
                #     output_field=IntegerField()
                # ))),
                "users": User.objects.all().order_by('first_name').values("id", "username", "email", "role_name"),
                "categories": ProductCategory.objects.all().values("id", "category", "description"),
                "sub_categories": ProductSubCategory.objects.all().values("id", "sub_category", category = F("product_category__category")),
                "devices_expire_in_30_days": Product.objects.filter(valid_till__gte=datetime.today(), valid_till__lte=datetime.today() + timedelta(days=30)).values("id", "product_code", sub_category = F("product_sub_category__sub_category"), category=F("product_sub_category__product_category__category")),
                # "ready_to_test": StructuredTestCases.objects.filter().values('product_id').all().distinct().values('id', "test_id", "test_name", "objective", "product_id", product_name = F("product__product_code"), test_type_name = F('test_type__code'), test_category_name = F("test_category__name")),
                "ready_to_test": StructuredTestCases.objects.filter().values('product_id').all().distinct().values("product_id", product_name = F("product__product_code"), sub_category = F("product__product_sub_category__sub_category"), category = F("product__product_category__category")),
            }
            choice = request.GET.get("chart_data_point", None)
            if not (choice or choice in registry.keys()):

                response = {
                    "status": 400,
                    "message": f"Please pass the chart_data_point to get chart data. Available chart data points are {registry.keys}",
                    "data": []
                }
                logger.log(level="ERROR", message=f"chart_data_point failed")
            response = {
                "status": 200,
                "message": "",
                "data": list(registry.get(choice, [])) if choice != 'users' else registry.get(choice, {})
            }
            logger.log(level='INFO', message=f'DashboardChart data fetched sucessfully.')
            return Response(response)
        except Exception as e:
            logger.log(level="ERROR", message=f"DashboardChart data fetching failed,{e}")
            return JsonResponse({'data': "Something went wrong"})


class UploadDeviceDocsView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)

    def post(self, request):
        try:
            files = request.FILES.getlist('pdf_files', [])  # Access multiple files
            files_uploaded = []
            files_not_uplaoded = []
            product_id = request.GET.get("device_id", "5")
            product = Product.objects.filter(id=product_id).first()
            if not product:
                logger.log(level="ERROR", message=f"product not found")
                return Response(
                    {
                        "status": 400,
                        "error_message": f"No device found with device_id {product_id}. Please pass valid device_id.",
                        "data": {}
                    }
                )
            product_name = product.product_code
            for f in files:
                temp_file = ContentFile(f.read())
                try:
                    filename = f.name  # Get original filename
                    bucket_name = 'genaidev'
                    key = f'devices/{product_name}/{filename}'
                    s3.put_object(Bucket=bucket_name, Key=key)  # Create subfolder with filename
                    s3.upload_fileobj(temp_file, bucket_name, key)  # Upload file to S3
                    files_uploaded.append(filename)
                    s3_url = f"https://{bucket_name}.s3.{AWS_DEFAULT_REGION}.amazonaws.com/{key}"
                    DocumentUploads.objects.create(
                        customer=request.user.customer,
                        created_by=request.user,
                        request_id=request.request_id,
                        product=product,
                        file_name=filename,
                        s3_url=s3_url
                    )
                except Exception as e:
                    files_not_uplaoded.append(f.name)
                    logger.log(level="ERROR", message=f"file uploaded failed,{f.name}")
            return Response({
                "status": 400 if len(files_not_uplaoded) else 200,
                "error_message": f"Some files {files_not_uplaoded} are not uploaded " if len(
                    files_not_uplaoded) else "All files are uploaded to s3 Succesfully",
                "data": {
                    "files_uploaded": files_uploaded,
                    "files_not_uploaded": files_not_uplaoded
                }
            })
        except Exception as e:
            logger.log(level="ERROR", message=f"files not uploaded,{e}")
            return JsonResponse({'data': "Something went wrong"})


class EmbedUploadedDocs(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)

    def get(self, request):
        try:
            if self.request.GET.get('run_cron', False):
                a = CronJob()
                a.performOperation()

            device_id = request.GET.get('device_id', None)
            device = Product.objects.filter(id=device_id).first()
            if not device:
                logger.log(level="ERROR", message=f"Device not found")
                return Response(
                    {
                        "status": 400,
                        "error_message": "Please pass valid device_id in queryparams",
                        "data": {}
                    }
                )
            CronExecution.objects.create(
                name="CREATE_VECTOR_EMBEDDINGS",
                customer=request.user.customer,
                created_by=request.user,
                params={
                    "device_id": device_id
                },
                request_id=request.request_id
            )
            logger.log(level='INFO', message=f'file data fetched sucessfully.')
            return Response(
                {
                    "status": 200,
                    "error_message": "",
                    "data": {
                        "message": "Creation of Embeddings will take atleast 20 mins."
                    }
                }
            )
        except Exception as e:
            logger.log(level="ERROR", message=f"fetching docs failed,{e}")
            return JsonResponse({'data': "Something went wrong"})


class ExtractTextFromPDFView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)

    def post(self, request, *args, **kwargs):
        try:
            bucket_name = request.GET.get('bucket_name')
            folder_path = request.GET.get('folder_path')
            result = extract_pdf(bucket_name=bucket_name, folder_path=folder_path)
            logger.log(level='INFO', message=f'Extract Text From PDF  inserted sucessfully.')
            return JsonResponse(result)
        except Exception as e:
            logger.log(level="ERROR", message=f"Extract Text From PDF  inserted failed,{e}")
            return JsonResponse({'data': "Something went wrong"})


class CategoryDetailsView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)

    def get(self, request):
        try:
            categories = ProductCategory.objects.all()
            category_data = []
            for category in categories:
                sub_category_count = ProductSubCategory.objects.filter(product_category_id=category.id).count()
                product_count = Product.objects.filter(product_category_id=category.id).count()
                category_data.append({
                    'category_name': category.category,
                    'sub_category_count': sub_category_count,
                    'device_count': product_count
                }
                )
            logger.log(level='INFO', message=f'fetching sucessfully CategoryDetails  .')
            return JsonResponse({"data": category_data, "status": 200})
        except Exception as e:
            logger.log(level="ERROR", message=f" fetching CategoryDetails failed,{e}")
            return JsonResponse({'data': "Something went wrong"})


class TestSubCategoriesView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)
    filterset_class = TestSubCategoriesFilter
    serializer_class = TestSubCategoriesSerializer
    ordering_fields = ['id', 'created_at', 'last_updated_at']
    ordering = []  # for default orderings

    def get_queryset(self, filters={}):
        try:
            return TestSubCategories.objects.filter(**filters)
        except Exception as e:
            logger.log(level="ERROR", message=f"Connectivity issues,{e}")
            return JsonResponse({'data': "Something went wrong"})

    def get(self, request, *args, **kwargs):
        try:
            filters = {"is_approved": True,
                       "status": True,
                       "test_type_id": request.query_params.get('test_type_id', None),
                       "test_category_id": request.query_params.get('test_category_id', None)}
            queryset = self.filter_queryset(self.get_queryset(filters))
            serializer = self.get_serializer(queryset, many=True)
            logger.log(level='INFO', message=f'TestSubCategories fetched sucessfully.')
            return JsonResponse({'data': serializer.data}, safe=False)
        except Exception as e:
            logger.log(level="ERROR", message=f"Error while retriving TestSubCategories,{e}")
            return JsonResponse({'data': "Something went wrong"})
        

class TestResponse(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        return Response("You are in get method")
    
    def post(self, request, *args, **kwargs):
        try:
            met = test_response(request)
            # return met
            return Response(met)
        except Exception as e:
            return Response(f"{e}")


class FilterStructuredTestScriptView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)

    def get(self, request, *args, **kwargs):
        try:
            request_id = request.GET.get("request_id")
            type_param = request.GET.get("type")

            if request_id and type_param:
                data = self.get_test_cases_by_request_id_and_type(request_id, type_param)
            elif request_id:
                data = self.get_test_cases_by_request_id(request_id)
            elif type_param:
                data = self.get_request_ids_by_type(type_param)
            else:
                data = self.get_filtered_groups()

            return JsonResponse({"data": data})
        except StructuredTestCases.DoesNotExist:
            logger.log(level='ERROR', message="StructuredTestCases not found.")
            return JsonResponse({'data': "StructuredTestCases not found"}, status=404)
        except Exception as e:
            logger.log(level='ERROR', message=f"Failed to generate FilteredTestCasesView data: {e}")
            return JsonResponse({'data': "Something went wrong"}, status=500)

    def get_test_cases_by_request_id_and_type(self, request_id, type_param):
        test_cases = StructuredTestCases.objects.filter(request_id=request_id).exclude(type=type_param).values('test_name')
        self.check_exists(test_cases)
        data = list(test_cases)
        logger.log(level='SUCCESS', message=f"Data fetched successfully with request_id: {request_id} and type: {type_param}.")
        return data

    def get_test_cases_by_request_id(self, request_id):
        test_cases = StructuredTestCases.objects.filter(request_id=request_id, type='TESTCASE').exclude(
            test_name__in=StructuredTestCases.objects.filter(request_id=request_id, type='TESTSCRIPT').values('test_name')
        ).values('id', 'test_name')
        self.check_exists(test_cases)
        data = list(test_cases)
        logger.log(level='SUCCESS', message=f"Data fetched successfully with request_id: {request_id}.")
        return data

    def get_request_ids_by_type(self, type_param):
        request_ids = StructuredTestCases.objects.exclude(type=type_param).values('request_id').distinct()
        self.check_exists(request_ids)
        data = list(request_ids)
        logger.log(level='SUCCESS', message=f"Data fetched successfully with type parameter: {type_param}.")
        return data

    def get_filtered_groups(self):
        grouped = StructuredTestCases.objects.values('request_id', 'test_name').annotate(
            type_count=Count('type', distinct=True),
            has_testcase=Count('type', filter=Q(type='TESTCASE')),
            has_testscript=Count('type', filter=Q(type='TESTSCRIPT'))
        )
        filtered_groups = grouped.filter(type_count=1, has_testcase=1, has_testscript=0)
        self.check_exists(filtered_groups)
        valid_request_ids = filtered_groups.values_list('request_id', flat=True).distinct()
        data = [{"request_id": rid} for rid in valid_request_ids]
        logger.log(level='SUCCESS', message="Data fetched successfully without parameters.")
        return data

    def check_exists(self, queryset):
        if not queryset.exists():
            raise StructuredTestCases.DoesNotExist

class TestSubCategoryParametersView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)

    def get(self, request):
        try:
            get_parameters = request.GET.get('get_parameters', False)
            if get_parameters:
                return self.get_paramters(request)
            
            test_sub_category_id = request.GET.get("test_sub_category_id", None)
            if not test_sub_category_id:
                raise Exception("Please pass test_sub_category_id")
            
            test_sub_category_parameters = TestSubCategoryParameters()
            result = test_sub_category_parameters.get(request, test_sub_category_id)
            return Response(result)
        except Exception as e:
            print(f"Error in get method: {e}")
            raise e
        
    def get_paramters(self, request):
        filters = {}
        sub_category_id = request.GET.get('test_sub_category_id',None)
        # if not sub_category_id:
        #     return Response({
        #         "errorMessage": "Please pass sub_category_id to get the parameters",
        #         "result" : {}
        #     })
        if sub_category_id is not None:
            filters['test_sub_category_id'] = sub_category_id
        paramters = Paramters.objects.filter(**filters)
        if not paramters:
            return Response({
                "errorMessage": "No paramters found with the test_sub_category_id {}".format(sub_category_id),
                "result": {}
            }, status=401)
        
        try:
            serializer = TestSubCategoryParamtersSerializer(paramters, many=True)
            data = serializer.data
            return Response({
                "errorMessage" : "",
                "result" : data
            }, status=200)
        except Exception as e:
            message = f"Error while getting the paramters for test sub category {paramters[0].test_sub_category.name}. ERROR:{e}"
            raise Exception(message)


class CsvFilesandItsColumnsView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)

    def get(self, request):
        try:
            pass
            # topology_id = request.GET.get('topology_id', "")
            bucket_name, prefix= "genaidev", "CSVFiles/"
            result = self.get_s3_csv_columns(bucket_name, prefix)
            return Response({
                "status": 200,
                "errorMessage":"",
                "result": result
            })
        except Exception as e:
            message = f"Error while getting the csv files and its columns. ERROR: {e}"
            raise Exception(message)
        
    def get_s3_csv_columns(self, bucket_name, prefix):
        result = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        files_info = []

        for obj in result.get('Contents', []):
            if obj['Key'].endswith('.csv'):
                csv_obj = s3.get_object(Bucket=bucket_name, Key=obj['Key'])
                body = csv_obj['Body'].read().decode('utf-8')
                df = pd.read_csv(StringIO(body))
                file_info = {
                    'file_name': obj['Key'].split('/')[-1],
                    's3_location': obj['Key'],
                    'bucket_name': bucket_name,
                    'columns': list(df.columns)
                }
                files_info.append(file_info)
        return files_info

class UpdateParametersAPI(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)

    def transform_join_keys_and_merge_columns(self, joinFilesItems, mergeColumnsItems):
        try:
            join_info = []
            merge_columns_info = {}

            for item in joinFilesItems:
                file_one_base = item['fileOne']['file_name'].split('.')[0]
                file_two_base = item['fileTwo']['file_name'].split('.')[0]
                
                join_condition = f"{file_one_base}.{item['fieldOne']}{item['condition']}{file_two_base}.{item['fieldTwo']}"
                join_info.append(join_condition)

            for item in mergeColumnsItems:
                file_base_name = item['fileName']['file_name'].split('.')[0]
                
                merge_columns_info[file_base_name] = {
                    item["newColumnHeader"]: {
                        "separator": item['separator'],
                        "columns_to_merge": [f"{file_base_name}.{col}" for col in item['mergeColumns']]
                    }
                }

            logger.log("Join keys and merge columns transformed successfully.")
            return {"join_info": join_info, "merge_columns_info": merge_columns_info}
        except Exception as e:
            logger.log(f"Error transforming join keys and merge columns: {e}")
            raise

    def transform_condition(self, condition):
        try:
            file_name = condition['fileName']['file_name'].split('.')[0]
            transformed_condition = {
                "check_key": f"{file_name}.{condition['columnTitle']}",
                "check_type": condition['condition'],
                "check_value": condition['columnValue'],
                "is_mandatory": condition['is_mandatory'],
                "skip_if_no_column": condition['skip_if_no_column']
            }
            logger.log(f"Condition transformed: {transformed_condition}")
            return transformed_condition
        except KeyError as e:
            logger.log(f"KeyError in condition: {e}, condition: {condition}")
            raise
        except Exception as e:
            logger.log(f"Unexpected error transforming condition: {e}, condition: {condition}")
            raise

    def transform_conditions(self, conditions, is_mandatory=True, skip_if_no_column=False):
        try:
            output = {"conditions": {}}
            for condition in conditions:
                main_condition_key = condition.get("mainCondition", "").lower()
                if "conditions" in condition:
                    nested_conditions = self.transform_conditions(condition["conditions"])["conditions"]
                    condition_data = {
                        "conditions": nested_conditions,
                        "is_mandatory": condition.get("is_mandatory", is_mandatory),
                        "skip_if_no_column": condition.get("skip_if_no_column", skip_if_no_column)
                    }
                else:
                    condition_data = self.transform_condition(condition)

                if main_condition_key not in output["conditions"]:
                    output["conditions"][main_condition_key] = []

                output["conditions"][main_condition_key].append(condition_data)

            output["is_mandatory"] = is_mandatory
            output["skip_if_no_column"] = skip_if_no_column
            
            logger.log("Conditions transformed successfully.")
            return output
        except KeyError as e:
            logger.log(f"KeyError in conditions: {e}, conditions: {conditions}")
            raise
        except Exception as e:
            logger.log(f"Unexpected error transforming conditions: {e}, conditions: {conditions}")
            raise
    
    def convert_requested_param_items(self, requested_param_items):
        required_params = []

        for item in requested_param_items:
            try:
                # Extract file base name and requested columns
                file_name = item['fileName']['file_name']
                file_base_name = file_name.split('.')[0]
                requested_columns = item['requestedColumns']

                # Extend the list with formatted columns
                required_params.extend([f"{file_base_name}.{column}" for column in requested_columns])
            
            except KeyError as e:
                logger.log(f"KeyError: {e} - Missing key in item: {item}")
                raise e
            except Exception as e:
                logger.log(f"An error occurred while processing item {item}: {e}")
                raise e

        return required_params
    
    def extract_from_joinFilesItems(self, data):
        def extract_file_keys(data):
            file_keys = []
            for item in data:
                for key in item.keys():
                    if key.startswith("file"):
                        file_keys.append(key)
            return file_keys
        
        file_info = set()
        keys_startswith_file = extract_file_keys(data)
        for item in data:
            for key in keys_startswith_file:
                bucket_name = item[key].get('bucket_name')
                s3_location = item[key].get('s3_location')
                if bucket_name and s3_location:
                    file_info.add((bucket_name, s3_location))
        return file_info

    def extract_from_mergeColumnsItems(self, data):
        file_info = set()
        for item in data:
            if 'fileName' in item and isinstance(item['fileName'], dict):
                bucket_name = item['fileName'].get('bucket_name')
                s3_location = item['fileName'].get('s3_location')
                if bucket_name and s3_location:
                    file_info.add((bucket_name, s3_location))
        return file_info

    def extract_files_info(self, filterConditionItems):
        s3_info_set = set()

        def add_s3_info(item):
            try:
                bucket_name = item['fileName'].get('bucket_name')
                s3_location = item['fileName'].get('s3_location')
                if bucket_name and s3_location:
                    s3_info_set.add((bucket_name, s3_location))
            except Exception as e:
                print(f"An error occurred while processing item {item}: {e}")

        for item in filterConditionItems:
            try:
                if 'conditions' in item:
                    for condition in item['conditions']:
                        add_s3_info(condition)
                else:
                    add_s3_info(item)
            except Exception as e:
                print(f"An error occurred while processing filterConditionItems item {item}: {e}")

        return s3_info_set


    def combine_file_info(self, join_files_items, merge_columns_items, filter_main_condition_items, requested_param_items):
        file_info = set()
        file_info.update(self.extract_from_joinFilesItems(join_files_items))
        file_info.update(self.extract_from_mergeColumnsItems(merge_columns_items))
        file_info.update(self.extract_files_info(filter_main_condition_items))
        file_info.update(self.extract_from_mergeColumnsItems(requested_param_items))
        return [{"bucket": bucket, "s3_key": s3_key} for bucket, s3_key in file_info]
    
    def post(self, request):
        try:
            join_files_items = request.data.get('joinFilesItems', [])
            merge_columns_items = request.data.get('mergeColumnsItems', [])
            filter_main_condition_items = request.data.get('filterConditionItems', [])
            requested_param_items = request.data.get('requestedParamItems', [])
            name = request.data.get('parameterName', 'EmptyParamter')
            description = request.data.get('description', '')
            customer_id = self.request.user.customer_id
            test_sub_category_id = request.data.get('subCategoryId',6)
            created_by_id = self.request.user.id
            last_updated_by_id = self.request.user.id
            logger.log("Received request data.")

            join_keys_and_merge_columns = self.transform_join_keys_and_merge_columns(
                join_files_items,
                merge_columns_items
            )
            filter_conditions = self.transform_conditions(
                filter_main_condition_items
            )
            required_params = self.convert_requested_param_items(requested_param_items)
            files_info_items = self.combine_file_info(join_files_items, merge_columns_items, filter_main_condition_items, requested_param_items)

            # print("join_keys_and_merge_columns : ",join_keys_and_merge_columns)
            # print("\nfilter_conditions : ",filter_conditions)
            # print("\nrequired_params : ",required_params)
            # print("\files_info_items : ",files_info_items)
            # print(f"\ncustomer_id : {customer_id}\ncreated_by_id : {created_by_id}\ntest_sub_category_id : {test_sub_category_id}")

            parameters = Paramters(
                name=name,
                description=description,
                join_keys=join_keys_and_merge_columns,
                conditions=filter_conditions,
                req_params = required_params,
                customer_id=customer_id,
                test_sub_category_id=test_sub_category_id,
                created_by_id=created_by_id,
                last_updated_by_id = last_updated_by_id,
                files_info = files_info_items
            )

            parameters.save()

            logger.log("Parameters saved successfully.")
            return Response({'status': 'success'}, status=201)

        except Exception as e:
            logger.log(f"Error in processing request: {e}")
            return Response({'status': 'error', 'message': str(e)}, status=400)

class ProcessConfigView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)

    def get(self, request, *args, **kwargs):
        process_network_config()
        return JsonResponse({'status': 'Processing started'})

class TopologyParamterSpecs(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)

    def get(self, reqeust):
        try:
            get_available_topology_param_specs = reqeust.GET.get('get_available_topology_param_specs', False)
            
            if get_available_topology_param_specs:
                paramters = self.get_available_topology_param()
            else:
                filters = {}
                topology_id = reqeust.GET.get('topology_id', None)
                test_sub_category = reqeust.GET.get('test_sub_category_id',None)

                if not(topology_id or test_sub_category): raise Exception("Pass topology_id or test_sub_category_id to get parameter specifications")
                if topology_id: filters['test_sub_category__test_type_id'] = topology_id
                if test_sub_category: filters['test_sub_category_id'] = test_sub_category
                paramters = self.get_queryset(filters)

            serializer = TestSubCategoryParamtersSerializer(paramters, many=True)
            data = serializer.data
            return Response({
                "errorMessage" : "",
                "result" : data
            }, status=200)
        except Exception as e:
            message = f"Error while getting topology parameter specifications. ERROR: {e}"
            raise Exception(message)
        
    def get_queryset(self, filters):
        return [Paramters.objects.filter(**filters).first()]
    
    def get_available_topology_param(self):
        data = Paramters.objects.values('id', topology_id = F('test_sub_category__test_type_id'))
        seen_topologies = {}
        for item in data:
            if item['topology_id'] not in seen_topologies:
                seen_topologies[item['topology_id']] = item['id']
        return Paramters.objects.filter(id__in = list(seen_topologies.values()))

