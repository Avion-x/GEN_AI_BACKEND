import asyncio
from collections import defaultdict
from datetime import date, datetime, timedelta
import threading
from product.services.aws_bedrock import AwsBedrock
from user.models import CustomerConfig, User
from product.services.custom_logger import logger
from product.services.github_service import push_to_github, get_commits_for_file, get_changes_in_file, \
    get_files_in_commit
from product.services.generic_services import get_prompts_for_device, get_string_from_datetime, parseModelDataToList, \
    validate_mandatory_checks
from product.filters import TestTypeFilter, ProductCategoryFilter
from rest_framework import generics, viewsets, filters as rest_filters
from django_filters import rest_framework as django_filters
from rest_framework.response import Response
from .models import StructuredTestCases, TestCases, TestType, ProductCategory, ProductSubCategory, Product, \
    TestScriptExecResults
from .serializers import TestTypeSerializer, ProductCategorySerializer, ProductSubCategorySerializer, ProductSerializer
from .filters import TestTypeFilter, ProductCategoryFilter, ProductSubCategoryFilter, ProductFilter, \
    LatestTestTypesWithCategoriesOfProductFilter
# import git
import os
from django.db.models import F, Q, Value, Count, Max, Min, JSONField, BooleanField, ExpressionWrapper, CharField, Case, \
    When, Sum, CharField, IntegerField
from django.db.models.functions import Cast

from .models import TestCases, TestType, ProductCategory, ProductSubCategory, Product, TestCategories, DocumentUploads
from .serializers import TestTypeSerializer, ProductCategorySerializer, ProductSubCategorySerializer, ProductSerializer, \
    TestCasesSerializer, TestCategoriesSerializer, TestScriptExecResultsSerializer
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
from io import BytesIO
from event_manager.models import CronExecution
from event_manager.service.cronjob import CronJob

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from botocore.exceptions import ClientError
from boto3.s3.transfer import S3Transfer

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

    def get_queryset(self, filters={}):
        return TestType.objects.filter(**filters)

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = TestTypeSerializer(queryset, many=True)
        return JsonResponse({'data': serializer.data}, safe=False)

    def post(self, request, *args, **kwargs):
        request.data['last_updated_by'] = self.request.user.username
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse({"message": "Test Type created successfully", "data": serializer.data, "status": 200})

    def put(self, request, *args, **kwargs):
        request.data['last_updated_by'] = self.request.user.username
        partial = kwargs.pop('partial', False)
        id = request.data.get('id')
        if not id:
            return Response({"message": "Please pass id to update Test Type", "status": 400})
        instance = self.get_queryset({"id": id}).first()
        if not instance:
            return JsonResponse({"message": "No Record found", "status": 400})
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse({"message": "Test Type updated successfully", "data": serializer.data, "status": 200})

    def delete(self, request, *args, **kwargs):
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
        return JsonResponse({"message": "Test Type deleted successfully", "status": 200})


class ProductCategoryView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)
    filterset_class = ProductCategoryFilter
    serializer_class = ProductCategorySerializer
    ordering_fields = ['id', 'created_at', 'last_updated_at']
    ordering = []  # for default orderings

    def get_queryset(self, filters={}):
        return ProductCategory.objects.filter(**filters)

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = ProductCategorySerializer(queryset, many=True)
        # return JsonResponse({'data':serializer.data}, safe=False)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        request.data['customer'] = self.request.user.customer_id
        request.data['last_updated_by'] = self.request.user.id
        request.data['created_by'] = self.request.user.id
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse({"message": "Category created successfully", "data": serializer.data, "status": 200})

    def put(self, request, *args, **kwargs):
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
        return JsonResponse({"message": "Category updated successfully", "data": serializer.data, "status": 200})

    def delete(self, request, *args, **kwargs):
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
        return JsonResponse({"message": "Category deleted successfully", "status": 200})


class ProductSubCategoryView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)
    filterset_class = ProductSubCategoryFilter
    serializer_class = ProductSubCategorySerializer
    ordering_fields = ['id', 'created_at', 'last_updated_at']
    ordering = []  # for default orderings

    def get_queryset(self, filters={}):
        return ProductSubCategory.objects.filter(**filters)

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = ProductSubCategorySerializer(queryset, many=True)
        logger.log(level="INFO", message="Product Sub Categories api")
        return JsonResponse({'data': serializer.data}, safe=False)

    def post(self, request, *args, **kwargs):
        request.data['customer'] = self.request.user.customer_id
        request.data['last_updated_by'] = self.request.user.id
        request.data['created_by'] = self.request.user.id
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse({"message": "Sub Category created successfully", "data": serializer.data, "status": 200})

    def put(self, request, *args, **kwargs):
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
        return JsonResponse({"message": "Sub Category updated successfully", "data": serializer.data, "status": 200})

    def delete(self, request, *args, **kwargs):
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
        return JsonResponse({"message": "Sub Category deleted successfully", "status": 200})


class ProductView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)
    filterset_class = ProductFilter
    serializer_class = ProductSerializer
    ordering_fields = ['id', 'created_at', 'last_updated_at']
    ordering = []  # for default orderings

    def get_queryset(self, filters={}):
        return Product.objects.filter(**filters)

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = ProductSerializer(queryset, many=True)
        non_empty = []
        data = serializer.data
        if request.GET.get('test_types_available', False):
            for key in data:
                if len(key['test_types']) != 0:
                    non_empty.append(key)
            data = non_empty
        return JsonResponse({'data': data}, safe=False)

    def post(self, request, *args, **kwargs):
        request.data['customer'] = self.request.user.customer_id
        request.data['last_updated_by'] = self.request.user.id
        request.data['created_by'] = self.request.user.id
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse({"message": "Product created successfully", "data": serializer.data, "status": 200})

    def put(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        id = request.data.get('id')
        if not id:
            return Response({"message": "Please pass id to update Product", "status": 400})
        instance = self.get_queryset({"id": id}).first()
        if not instance:
            return JsonResponse({"message": "No Record found", "status": 400})
        request.data['customer'] = self.request.user.customer_id
        request.data['last_updated_by'] = self.request.user.id
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse({"message": "Product updated successfully", "data": serializer.data, "status": 200})

    def delete(self, request, *args, **kwargs):
        id = request.GET.get('id')
        if not id:
            return Response({"message": "Please pass id to delete Product", "status": 400})
        instance = self.get_queryset({"id": id}).first()
        if not instance:
            return JsonResponse({"message": "No Record found", "status": 400})
        instance.status = 0
        instance.last_updated_by = self.request.user
        instance.save()
        return JsonResponse({"message": "Product deleted successfully", "status": 200})


class GenerateTestCases(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    validation_checks = {
        "device_id": {
            "is_mandatory": True,
            "type": str,
            "convert_type": True,
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
    AiModels = {
        "open_ai": CustomOpenAI,
        "anthropic.claude-v2:1": AwsBedrock,
        "anthropic.claude-v2": AwsBedrock,
        'amazon.titan-text-express-v1': AwsBedrock,
    }

    def set_device(self, device_id):
        try:
            self.device = Product.objects.get(id=device_id)
        except Exception as e:
            raise e

    def get_ai_obj(self, data):
        try:
            model = data.get('ai_model', "open_ai")
            ai_model = self.AiModels.get(model, None)
            if not ai_model:
                message = f"Please provide valid ai_model, Available models are {list(self.AiModels.keys())}"
                logger.log(level="ERROR", message=message)
                raise Exception(message)
            return ai_model(modelId=model)
        except Exception as e:
            raise e

    def post(self, request):
        try:
            data = validate_mandatory_checks(input_data=request.data, checks=self.validation_checks)
            self.ai_obj = self.get_ai_obj(data)
            self.set_device(data['device_id'])
            prompts_data = get_prompts_for_device(**data)

            print(prompts_data)

            self.lang_chain = Langchain_(prompt_data=prompts_data, request=request)

            thread = threading.Thread(target=self.process_request, args=(request, prompts_data))
            thread.start()

            # self.process_request(request, prompts_data)

            response = {
                "request_id": request.request_id,
                "Message": "Processing request will take some time Please come here in 5 mins",
            }
            return Response({
                "error": "",
                "status": 200,
                "response": response
            })

        except Exception as e:
            # request.request_tracking.status_code = 400
            # request.request_tracking.error_message = str(e)
            # request.request_tracking.save()
            return Response({
                "error": f"{e}",
                "status": 400,
                "response": {}
            })

    def process_request(self, request, prompts_data):
        try:
            response = {}
            for test_type, tests in prompts_data.items():
                response[test_type] = {}
                for test, test_data in tests.items():
                    response[test_type][test] = self.execute(request, test_type, test, test_data)
            return response
        except Exception as e:
            raise e

    def execute(self, request, test_type, test_category, input_data):
        try:
            response = {}
            insert_data = {"test_category_id": input_data.pop("test_category_id", None), "device_id": self.device.id,
                           "prompts": input_data}
            for test_code, details in input_data.items():
                kb_data = self.lang_chain.execute_kb_queries(details.get('kb_query', []))
                print("\n\n kb data is :", kb_data)
                prompts = details.get('prompts', [])

                file_path = self.get_file_path(request, test_type, test_category, test_code)
                response[test_code] = self.generate_tests(prompts=prompts, context=kb_data)
                self.store_parsed_tests(request=request, data = response[test_code], test_type=test_type, test_category=test_category, test_category_id=insert_data.get("test_category_id"))
                insert_data['git_data'] = push_to_github(data=response[test_code].pop('raw_text', ""), file_path=file_path)
                insert_test_case(request, data=insert_data.copy())
            # response['test_category'] = test_category
            return response
        except Exception as e:
            raise e

    # def execute(self, request, test_type, test_category, input_data):
    #     try:
    #         response = {}
    #         insert_data = {"test_category_id": input_data.pop("test_category_id", None), "device_id": self.device.id,
    #                        "prompts": input_data}
    #         for test_code, propmts in input_data.items():
    #             file_path = self.get_file_path(request, test_type, test_category, test_code)
    #             response[test_code] = self.generate_tests(prompts=propmts)
    #             self.store_parsed_tests(request=request, data = response[test_code], test_type=test_type, test_category=test_category, test_category_id=insert_data.get("test_category_id"))
    #             insert_data['git_data'] = push_to_github(data=response[test_code].pop('raw_text', ""), file_path=file_path)
    #             insert_test_case(request, data=insert_data.copy())
    #         # response['test_category'] = test_category
    #         return response
    #     except Exception as e:
    #         raise e

    def store_parsed_tests(self, request, data, test_type, test_category, test_category_id):
        for test_case, test_script in zip(data.get('test_cases', []), data.get('test_scripts', [])):
            name = test_case.get('testname', test_case.get('name', "")).replace(" ", "_").lower()
            test_id = f"{request.user.customer.name}_{test_type}_{test_category}_{self.device.product_code}_{name}".replace(
                " ", "_").lower()
            _test_case = {
                "test_id": test_id,
                "test_name": f"{name}",
                "objective": test_case.get("objective", ""),
                "data": test_case,
                "type": "TESTCASE",
                "test_category_id": test_category_id,
                "product": self.device,
                "customer": request.user.customer,
                "request_id": self.request.request_id,
                "created_by": request.user
            }

            _test_script = {
                "test_id": test_id,
                "test_name": f"{name}",
                "objective": test_script.get("objective", ""),
                "data": test_script,
                "type": "TESTSCRIPT",
                "test_category_id": test_category_id,
                "product": self.device,
                "customer": request.user.customer,
                "request_id": self.request.request_id,
                "created_by": request.user
            }

            StructuredTestCases.objects.create(**_test_case)
            StructuredTestCases.objects.create(**_test_script)
        return True

    # def store_in_github(self, data, file_path ):
    #     response = []
    #     registry = {
    #         'raw' : "raw.md",
    #         'test_cases': "TestCases.md",
    #         'test_scripts': "TestScripts.py",
    #     }
    #     for key, file_name in registry.items():
    #         pass

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

    def generate_tests(self, prompts, context, **kwargs):
        try:
            response_text = ""
            for prompt in prompts:
                kwargs['prompt'] = prompt
                kwargs['context'] = context
                prompt_data = self.ai_obj.send_prompt(**kwargs)
                response_text += prompt_data
            return self.get_test_data(response_text)
        except Exception as e:
            raise e

    def get_test_data(self, text_data):
        result = {"raw_text": text_data, "test_cases": [], "test_scripts": []}
        data = parseModelDataToList(text_data)
        for _test in data:
            test_case = _test.get('testcase', None)
            test_scripts = _test.get('testscript', None)
            if test_case and test_scripts:
                if isinstance(test_case, list):
                    result['test_cases'] += test_case
                else:
                    result['test_cases'].append(test_case)

                if isinstance(test_scripts, list):
                    result['test_scripts'] += test_scripts
                else:
                    result['test_scripts'].append(test_scripts)
        return result


def insert_test_case(request, data):
    try:
        record = {
            "customer": request.user.customer,
            "product_id": data.pop("device_id"),
            "created_by": request.user,
            "data_url": data.get('git_data').get("url"),
            "sha": data.get('git_data').get("sha"),
            "test_category_id": data.pop("test_category_id"),
            "data": data,
            "request_id": request.request_id

        }
        return TestCases.objects.create(**record)
    except Exception as e:
        raise Exception(e)


class TestCasesAndScripts(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)
    # filterset_class = TestCasesFilter
    ordering_fields = ['id', 'created_at', 'updated_at']

    def get_queryset(self, filters={}):
        return StructuredTestCases.objects.filter(**filters)

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
            return Response({"data": data})
        except Exception as e:
            raise e

    def get_test_types_with_categories(self, filters):
        queryset = self.get_queryset(filters).values("test_category_id").annotate(
            count=Count(F("test_category_id"))).values("test_category_id", "request_id", test_id=F("test_type_id"),
                                                       test_name=F("test_type__code"),
                                                       category_name=F("test_category__name")).order_by("test_type")

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

        return list(test_data.values())

    def get_consolidated_data_of_test_category(self, queryset):

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

        return serialized_data


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
            return JsonResponse({'data': categories}, safe=False)
        except Exception as e:
            logger.log(level='Error', message=f"{e}")
            raise e


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
            logger.log(level='Error', message=f"{e}")
            raise e


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
        queryset = self.filter_queryset(self.get_queryset())
        serializer = TestCasesSerializer(queryset, many=True)
        return JsonResponse({'data': serializer.data}, safe=False)


class GetFileCommitsView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)

    def get(self, request):
        file_path = request.query_params.get('file_path')
        repo = request.query_params.get('repo')
        response_data = get_commits_for_file(file_path=file_path, repo=repo)
        return JsonResponse(response_data, safe=False)


class GetFileChangesView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)

    def get(self, request):
        file_name = request.query_params.get('file_name')
        sha = request.query_params.get('sha')
        response_data = get_changes_in_file(file_name=file_name, commit_sha=sha)
        return JsonResponse({"data": response_data}, safe=False)


class GetFilesInCommitView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)

    def get(self, request):
        sha = request.query_params.get('sha')
        response_data = get_files_in_commit(sha)
        return JsonResponse(response_data, safe=False)


class TestCategoriesView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)
    filterset_class = TestCategoriesFilter
    serializer_class = TestCategoriesSerializer
    ordering_fields = ['id', 'created_at', 'last_updated_at']
    ordering = []  # for default orderings

    def get_queryset(self, filters={}):
        return TestCategories.objects.filter(**filters)

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse({'data': serializer.data}, safe=False)

    def post(self, request, *args, **kwargs):
        request.data['customer'] = request.user.customer.id
        request.data['last_updated_by'] = request.user.id
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
        return JsonResponse({"message": "Test Category created successfully", "data": serializer.data, "status": 200})

    def put(self, request, *args, **kwargs):
        request.data['customer'] = request.user.customer.id
        request.data['last_updated_by'] = request.user.id
        partial = kwargs.pop('partial', False)
        id = request.data.get('id')
        if not id:
            return Response({"message": "Please pass id to update Test Category", "status": 400})
        instance = self.get_queryset({"id": id}).first()
        if not instance:
            return JsonResponse({"message": "No Record found", "status": 400})
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse({"message": "Test Category updated successfully", "data": serializer.data, "status": 200})

    def delete(self, request, *args, **kwargs):
        id = request.GET.get('id')
        if not id:
            return Response({"message": "Please pass id to delete Test Category", "status": 400})
        instance = self.get_queryset({"id": id}).first()
        if not instance:
            return JsonResponse({"message": "No Record found", "status": 400})
        instance.status = 0
        instance.last_updated_by = self.request.user
        instance.save()
        return JsonResponse({"message": "Test Category deleted successfully", "status": 200})


class TestScriptExecResultsView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)
    filterset_class = TestExecutionResultsFilter
    ordering_fields = ['id', 'created_at']
    ordering = []

    def get_queryset(self):
        return TestScriptExecResults.objects.filter(status=1,
                                                    test_script_number=self.request.data.get('test_script_number'))

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = TestScriptExecResultsSerializer(queryset, many=True)
        return JsonResponse({'data': serializer.data}, safe=False)


class DashboardKpi(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)

    def get(self, request):
        total_devices = Product.objects.all().count()
        test_types = TestType.objects.all().count()
        users = User.objects.all().count()
        categories = ProductCategory.objects.all().count()
        sub_categories = ProductSubCategory.objects.all().count()
        devices_expire_in_30_days = Product.objects.filter(valid_till__gte=datetime.today(),
                                                           valid_till__lte=datetime.today() + timedelta(
                                                               days=30)).count()
        ready_to_test = StructuredTestCases.objects.filter().values('product_id').all().distinct().count()
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


class PendingApprovalTestCategoryView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)
    filterset_class = TestCategoriesFilter
    serializer_class = TestCategoriesSerializer
    ordering_fields = ['id', 'created_at', 'last_updated_at']
    ordering = []  # for default orderings

    def get_queryset(self, filters={}):
        return TestCategories.objects.filter(**filters)

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset({"is_approved": False}))
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse({'data': serializer.data}, safe=False)


class ApproveTestCategoryView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    filter_backends = (django_filters.DjangoFilterBackend,)
    filterset_class = TestCategoriesFilter
    serializer_class = TestCategoriesSerializer
    ordering_fields = ['id', 'created_at', 'last_updated_at']
    ordering = []  # for default orderings

    def get_queryset(self, filters={}):
        return TestCategories.objects.filter(**filters)

    def put(self, request, *args, **kwargs):
        id = request.GET.get('id')
        if not id:
            return Response({"message": "Please pass id to Approve Test Category", "status": 400})
        instance = self.get_queryset({"id": id}).first()
        if not instance:
            return JsonResponse({"message": "No Record found", "status": 400})
        instance.is_approved = True
        instance.approved_by = self.request.user
        instance.save()
        return JsonResponse({"message": "Test Category Approved successfully", "status": 200})


class DashboardChart(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)

    def get(self, request):
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
        response = {
            "status": 200,
            "message": "",
            "data": list(registry.get(choice, [])) if choice != 'users' else registry.get(choice, {})
        }
        return Response(response)


class UploadDeviceDocsView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)

    def post(self, request):
        files = request.FILES.getlist('pdf_files', [])  # Access multiple files
        files_uploaded = []
        files_not_uplaoded = []
        product_id = request.GET.get("device_id", "5")
        product = Product.objects.filter(id = product_id).first()
        if not product:
            return Response(
                {
                    "status" : 400,
                    "error_message" : f"No device found with device_id {product_id}. Please pass valid device_id.",
                    "data" : {}
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
                    customer = request.user.customer,
                    created_by = request.user,
                    request_id = request.request_id,
                    product = product,
                    file_name = filename,
                    s3_url= s3_url
                )
            except Exception as e:
                print(e)
                files_not_uplaoded.append(f.name)
        
        return Response({
            "status" : 400 if len(files_not_uplaoded) else 200,
            "error_message" : f"Some files {files_not_uplaoded} are not uploaded " if len(files_not_uplaoded) else "All files are uploaded to s3 Succesfully",
            "data" : {
                "files_uploaded" : files_uploaded,
                "files_not_uploaded" : files_not_uplaoded
            }
        })

class EmbedUploadedDocs(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)

    def get(self, request):
        if self.request.GET.get('run_cron', False):
            a = CronJob()
            a.performOperation()

        device_id = request.GET.get('device_id', None)
        device = Product.objects.filter(id = device_id).first()
        if not device:
            return Response(
                {
                    "status" : 400,
                    "error_message" : "Please pass valid device_id in queryparams",
                    "data" : {}
                }
            )
        CronExecution.objects.create(
            name = "CREATE_VECTOR_EMBEDDINGS",
            customer = request.user.customer,
            created_by = request.user,
            params = {
                "device_id" : device_id
            },
            request_id = request.request_id
        )
        return Response(
            {
                "status" : 200,
                "error_message" : "",
                "data" : {
                    "message" : "Creation of Embeddings will take atleast 20 mins."
                }
            }
        )


class ExtractTextFromPDFView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)

    # Function to extract table as matrix
    def extract_table_as_matrix(self, page):
        table = page.extract_table()
        if table is None:
            return None

        # Convert table to matrix
        matrix = []
        for row in table:
            matrix_row = []
            for cell in row:
                if cell:
                    matrix_row.append(cell)
            if matrix_row:
                matrix.append(matrix_row)

        return matrix

    def post(self, request, *args, **kwargs):
        bucket_name = 'testmx480'

        # Establish connection with S3
        s3 = boto3.client('s3', aws_access_key_id='AKIA3MUTZS7BNCEROH24',
                          aws_secret_access_key='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', region_name='us-west-2')
        pdf_file_name = request.GET.get('file_name')

        # Download PDF from S3
        s3_response_object = s3.get_object(Bucket=bucket_name, Key=pdf_file_name)
        pdf_content = s3_response_object['Body'].read()

        # Process PDF content and write to S3
        with pdfplumber.open(BytesIO(pdf_content)) as pdf:
            processed_text = ""
            for page in pdf.pages:
                string = ""
                # Extract text from the page
                text = page.extract_text()
                processed_text += text + "\n"
                matrix = self.extract_table_as_matrix(page)
                if matrix:
                    for row in matrix[1:-1]:
                        # Iterate over each column other than the first one
                        for i in range(1, len(row)):
                            string += f"{matrix[0][0]}, {row[0]}, {matrix[0][i]}, {row[i]},"
                    if string:
                        processed_text += string[:-1] + "\n"

        # Convert processed text to BytesIO object
        processed_text_bytes = BytesIO(processed_text.encode('utf-8'))
        file_name = 'transcript-' + str(datetime.today()) + '.txt'

        try:
            # Upload the processed file directly to S3
            s3.put_object(Bucket=bucket_name, Key=file_name, Body=processed_text_bytes)
            return JsonResponse({"message": "File extracted and uploaded to s3 successfully", "status": 200})
        except Exception as e:
            return JsonResponse({"message": "File extraction failed", "status": 400})


class CategoryDetailsView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, TokenAuthentication)

    def get(self, request):
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
        return JsonResponse({"data": category_data, "status": 200})
