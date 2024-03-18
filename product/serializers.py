from rest_framework import serializers
from .models import TestType, ProductCategory, Product, ProductCategoryPrompt, ProductCategoryPromptCode, ProductPrompt, \
    ProductSubCategory, Prompt, TestCases, TestCategories, Customer, TestScriptExecResults
from django.contrib.auth.hashers import make_password

from django.db.models import F

class TestTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestType
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    main_category_id = serializers.SerializerMethodField()
    # sub_category_id = serializers.IntegerField(source='product_sub_category')
    main_category_name = serializers.SerializerMethodField()
    sub_category_name = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    test_types = serializers.SerializerMethodField()

    class Meta:
        model = Product
        # fields = '__all__'
        exclude = ['prompts']
    
    def get_test_types(self,obj):
        data = obj.structured_test_cases.values("test_type_id", name = F("test_type__code")).distinct()
        return list(data)

    def get_main_category_id(self, obj):
        return obj.product_sub_category.product_category.id
    
    def get_sub_category_name(self, obj):
        return obj.product_sub_category.sub_category

    def get_main_category_name(self, obj):
        return obj.product_sub_category.product_category.category

    def get_customer_name(self, obj):
        return obj.customer.name


class ProductSubCategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    main_category_id = serializers.SerializerMethodField()
    main_category_name = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()

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


class ProductCategorySerializer(serializers.ModelSerializer):
    sub_category_count = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = ProductCategory
        # fields = '__all__'
        exclude = ['prompts']

    def get_sub_category_count(self, obj):
        return obj.product_sub_category.count()

    def get_customer_name(self, obj):
        return obj.customer.name


class TestCasesSerializer(serializers.ModelSerializer):
    test_type_name = serializers.SerializerMethodField()
    test_category_name = serializers.SerializerMethodField()
    product_code = serializers.SerializerMethodField()
    sub_category_name = serializers.SerializerMethodField()
    main_category_name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()

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


class TestCategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCategories
        fields = '__all__'
        read_only_fields = ('approved_by',)  # Assuming you don't want this field to be modified directly

    def validate(self, data):
        # If is_approved is not provided, approved_by should also be cleared
        if 'is_approved' in data and not data.get('is_approved', False):
            data['approved_by'] = None
        return data


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


class TestScriptExecResultsSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    customer = serializers.SerializerMethodField()
    test_type = serializers.SerializerMethodField()
    test_category = serializers.SerializerMethodField()
    executed_by = serializers.SerializerMethodField()

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

    class Meta:
        model = TestScriptExecResults
        fields = ['test_script_number', 'execution_result_details', 'product', 'customer', 'test_type', 'test_category',
                  'executed_by']
