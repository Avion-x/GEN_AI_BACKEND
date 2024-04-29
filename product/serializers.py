from rest_framework import serializers

from event_manager.models import CronExecution
from .models import TestType, ProductCategory, Product, ProductCategoryPrompt, ProductCategoryPromptCode, ProductPrompt, \
    ProductSubCategory, Prompt, TestCases, TestCategories, Customer, TestScriptExecResults, UserCreatedTestCases, TestSubCategories
from django.contrib.auth.hashers import make_password
from django.db.models import F
import pytz
from product.services.custom_logger import logger


class ISTTimestamp:
    def get_ist_timestamp(self, timestamp):
        utc_timestamp = timestamp.astimezone(pytz.utc)
        ist_timestamp = utc_timestamp.astimezone(pytz.timezone('Asia/Kolkata'))
        formatted_timestamp = ist_timestamp.strftime("%Y-%m-%d %H:%M")
        return formatted_timestamp


class TestTypeSerializer(serializers.ModelSerializer, ISTTimestamp):
    created_at = serializers.SerializerMethodField()
    last_updated_at = serializers.SerializerMethodField()
    test_categories_count = serializers.SerializerMethodField()

    class Meta:
        model = TestType
        fields = '__all__'

    def get_created_at(self, obj):
        timestamp = obj.created_at
        ist_timestamp = self.get_ist_timestamp(timestamp)
        return ist_timestamp

    def get_last_updated_at(self, obj):
        timestamp = obj.last_updated_at
        ist_timestamp = self.get_ist_timestamp(timestamp)
        return ist_timestamp
    
    def get_test_categories_count(self, obj):
        return obj.test_category.count()


class ProductSerializer(serializers.ModelSerializer, ISTTimestamp):
    main_category_id = serializers.SerializerMethodField()
    # sub_category_id = serializers.IntegerField(source='product_sub_category')
    main_category_name = serializers.SerializerMethodField()
    sub_category_name = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    test_types = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    last_updated_at = serializers.SerializerMethodField()
    last_updated_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Product
        # fields = '__all__'
        exclude = ['prompts']

    def get_test_types(self, obj):
        data = obj.structured_test_cases.values("test_type_id", name=F("test_type__code")).distinct()
        return list(data)

    def get_main_category_id(self, obj):
        return obj.product_sub_category.product_category.id

    def get_sub_category_name(self, obj):
        return obj.product_sub_category.sub_category

    def get_main_category_name(self, obj):
        return obj.product_sub_category.product_category.category

    def get_customer_name(self, obj):
        return obj.customer.name

    def get_created_at(self, obj):
        timestamp = obj.created_at
        ist_timestamp = self.get_ist_timestamp(timestamp)
        return ist_timestamp

    def get_created_by_name(self, obj):
        return obj.created_by.username

    def get_last_updated_at(self, obj):
        timestamp = obj.last_updated_at
        ist_timestamp = self.get_ist_timestamp(timestamp)
        return ist_timestamp

    def get_last_updated_by_name(self, obj):
        return obj.last_updated_by.username


class ProductSubCategorySerializer(serializers.ModelSerializer, ISTTimestamp):
    product_count = serializers.SerializerMethodField()
    main_category_id = serializers.SerializerMethodField()
    main_category_name = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    last_updated_at = serializers.SerializerMethodField()
    last_updated_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ProductSubCategory
        fields = '__all__'

    def get_product_count(self, obj):
        return obj.product.count()

    def get_main_category_name(self, obj):
        return obj.product_category.category

    def get_main_category_id(self, obj):
        return obj.product_category.id

    def get_customer_name(self, obj):
        return obj.customer.name

    def get_created_at(self, obj):
        timestamp = obj.created_at
        ist_timestamp = self.get_ist_timestamp(timestamp)
        return ist_timestamp
    
    def get_created_by_name(self, obj):
        return obj.created_by.username

    def get_last_updated_at(self, obj):
        timestamp = obj.last_updated_at
        ist_timestamp = self.get_ist_timestamp(timestamp)
        return ist_timestamp

    def get_last_updated_by_name(self, obj):
        return obj.last_updated_by.username


class ProductCategorySerializer(serializers.ModelSerializer, ISTTimestamp):
    sub_category_count = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    last_updated_at = serializers.SerializerMethodField()
    last_updated_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ProductCategory
        # fields = '__all__'
        exclude = ['prompts']

    def get_sub_category_count(self, obj):
        return obj.product_sub_category.count()

    def get_customer_name(self, obj):
        return obj.customer.name

    def get_created_at(self, obj):
        timestamp = obj.created_at
        ist_timestamp = self.get_ist_timestamp(timestamp)
        return ist_timestamp
    
    def get_created_by_name(self, obj):
        return obj.created_by.username

    def get_last_updated_at(self, obj):
        timestamp = obj.last_updated_at
        ist_timestamp = self.get_ist_timestamp(timestamp)
        return ist_timestamp

    def get_last_updated_by_name(self, obj):
        return obj.last_updated_by.username

class UserCreatedTestCasesSerializer(serializers.ModelSerializer, ISTTimestamp):
    test_type_name = serializers.SerializerMethodField()
    test_category_name = serializers.SerializerMethodField()
    product_code = serializers.SerializerMethodField()
    sub_category_name = serializers.SerializerMethodField()
    main_category_name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    last_updated_at = serializers.SerializerMethodField()

    class Meta:
        model = UserCreatedTestCases
        fields = '__all__'

    def get_test_type_name(self, obj):
        return obj.test_category.test_type.code

    def get_test_category_name(self, obj):
        return obj.test_category.name

    def get_product_code(self, obj):
        return obj.product.product_code

    def get_sub_category_name(self, obj):
        return obj.product.product_sub_category.sub_category

    def get_main_category_name(self, obj):
        return obj.product.product_sub_category.product_category.category

    def get_username(self, obj):
        return obj.created_by.username

    def get_created_at(self, obj):
        timestamp = obj.created_at
        ist_timestamp = self.get_ist_timestamp(timestamp)
        return ist_timestamp

    def get_last_updated_at(self, obj):
        timestamp = obj.last_updated_at
        ist_timestamp = self.get_ist_timestamp(timestamp)
        return ist_timestamp

class TestCasesSerializer(serializers.ModelSerializer, ISTTimestamp):
    test_type_name = serializers.SerializerMethodField()
    test_category_name = serializers.SerializerMethodField()
    product_code = serializers.SerializerMethodField()
    sub_category_name = serializers.SerializerMethodField()
    main_category_name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    last_updated_at = serializers.SerializerMethodField()

    class Meta:
        model = TestCases
        fields = '__all__'

    def get_test_type_name(self, obj):
        return obj.test_category.test_type.code

    def get_test_category_name(self, obj):
        return obj.test_category.name

    def get_product_code(self, obj):
        return obj.product.product_code

    def get_sub_category_name(self, obj):
        return obj.product.product_sub_category.sub_category

    def get_main_category_name(self, obj):
        return obj.product.product_sub_category.product_category.category

    def get_username(self, obj):
        return obj.created_by.username

    def get_created_at(self, obj):
        timestamp = obj.created_at
        ist_timestamp = self.get_ist_timestamp(timestamp)
        return ist_timestamp

    def get_last_updated_at(self, obj):
        timestamp = obj.last_updated_at
        ist_timestamp = self.get_ist_timestamp(timestamp)
        return ist_timestamp


class TestCategoriesSerializer(serializers.ModelSerializer, ISTTimestamp):
    created_at = serializers.SerializerMethodField()
    last_updated_at = serializers.SerializerMethodField()
    last_updated_by_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()
    test_type_name = serializers.SerializerMethodField()

    class Meta:
        model = TestCategories
        fields = '__all__'

    def get_created_at(self, obj):
        timestamp = obj.created_at
        ist_timestamp = self.get_ist_timestamp(timestamp)
        return ist_timestamp

    def get_last_updated_at(self, obj):
        timestamp = obj.last_updated_at
        ist_timestamp = self.get_ist_timestamp(timestamp)
        return ist_timestamp

    def get_last_updated_by_name(self, obj):
        return obj.last_updated_by.username

    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return obj.approved_by.username
        else:
            return obj.approved_by

    def get_test_type_name(self, obj):
        return obj.test_type.code


class PromptSerializer(serializers.ModelSerializer):
    prompt_pro = serializers.SerializerMethodField()

    class Meta:
        model = Prompt
        fields = ['prompt', 'id']
        # exclude = ['provider', 'foundation_model', 'rag']

    def prompt_pro(self, obj):
        return obj.Prompt.prompt

    def prompt_pro_id(self, obj):
        return obj.Prompt.id


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['name', 'code', 'id']


class ProductCategoryPromptCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategoryPromptCode
        fields = '_all_'


class TestScriptExecResultsSerializer(serializers.ModelSerializer, ISTTimestamp):
    product = serializers.SerializerMethodField()
    customer = serializers.SerializerMethodField()
    test_type = serializers.SerializerMethodField()
    test_category = serializers.SerializerMethodField()
    executed_by = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    last_updated_at = serializers.SerializerMethodField()

    def get_product(self, obj):
        return obj.product.product_code

    def get_customer(self, obj):
        return obj.customer.code

    def get_test_type(self, obj):
        return obj.test_type.code

    def get_test_category(self, obj):
        return obj.test_category.name

    def get_executed_by(self, obj):
        return obj.created_by.username

    def get_created_at(self, obj):
        timestamp = obj.created_at
        ist_timestamp = self.get_ist_timestamp(timestamp)
        return ist_timestamp

    def get_last_updated_at(self, obj):
        timestamp = obj.last_updated_at
        ist_timestamp = self.get_ist_timestamp(timestamp)
        return ist_timestamp

    class Meta:
        model = TestScriptExecResults
        fields = ['test_script_number', 'execution_result_details', 'product', 'customer', 'test_type', 'test_category',
                  'executed_by']



class GenereateTestCaseJobDataSerializer(serializers.ModelSerializer, ISTTimestamp):
    device_name = serializers.SerializerMethodField()
    device_id = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()
    execution_result = serializers.SerializerMethodField()
    
    class Meta:
        model = CronExecution
        fields = ['request_id', 'execution_status', 'device_id', 'device_name', 'data', 'execution_result', 'created_at', 'created_by', "created_by_name"]

    def __init__(self, *args, **kwargs):
        exclude_fields = kwargs.pop('exclude_fields', [])
        super(GenereateTestCaseJobDataSerializer, self).__init__(*args, **kwargs)
        for field_name in exclude_fields:
            self.fields.pop(field_name, None)

    def get_execution_result(self, obj):
        data = obj.results
        return data
        # for 

    def get_device_id(self, obj):
        return obj.params.get('body', {}).get('device_id', None)

    def get_device_name(self, obj):
        try:
            device_id = obj.params.get('body', {}).get('device_id', None)
            if device_id:
                return Product.objects.get(id=device_id).product_code
        except Exception as e:
            logger.log(level="ERROR", message=f"Error in getting device name from device id {device_id}. Error is {e}")
            return ""
    
    def get_data(self, obj):
        data = obj.params.get('body', {})
        _data = []
        _test_data = data.get('test_type_data',{})
        for test_data in _test_data:
            test_type_id = test_data.get('test_type_id', None)
            test_category_data = test_data.get('test_category_ids', {})
            test_category_ids = test_category_data.get('test_category_id', [])
            test_sub_category_ids = test_category_data.get('test_sub_categoy_ids', [])
            _data.append({
                "test_type_id": test_type_id,
                "test_type_name" : TestType.objects.get(id=test_type_id).code,
                "test_category_data": [TestCategories.objects.filter(id__in=test_category_ids).values("id", "name")],
                "test_sub_category_data": [ProductSubCategory.objects.filter(id__in=test_sub_category_ids).values("id", "sub_category")]
            })
        return _data
    
    def get_created_by_name(self, obj):
        return obj.created_by.username

    def get_created_at(self, obj):
        timestamp = obj.created_at
        ist_timestamp = self.get_ist_timestamp(timestamp)
        return ist_timestamp

class TestSubCategoriesSerializer(serializers.ModelSerializer, ISTTimestamp):
    created_at = serializers.SerializerMethodField()
    last_updated_at = serializers.SerializerMethodField()
    last_updated_by_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()
    test_type_name = serializers.SerializerMethodField()
    test_category_name = serializers.SerializerMethodField()

    class Meta:
        model = TestSubCategories
        fields = '__all__'

    def get_created_at(self, obj):
        timestamp = obj.created_at
        ist_timestamp = self.get_ist_timestamp(timestamp)
        return ist_timestamp

    def get_last_updated_at(self, obj):
        timestamp = obj.last_updated_at
        ist_timestamp = self.get_ist_timestamp(timestamp)
        return ist_timestamp

    def get_last_updated_by_name(self, obj):
        return obj.last_updated_by.username

    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return obj.approved_by.username
        else:
            return obj.approved_by

    def get_test_type_name(self, obj):
        return obj.test_type.code

    def get_test_category_name(self, obj):
        return obj.test_category.name