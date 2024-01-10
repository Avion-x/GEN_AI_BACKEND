from rest_framework import serializers
from .models import TestType, ProductCategory, Product, ProductCategoryPrompt, ProductCategoryPromptCode, ProductPrompt, ProductSubCategory, Prompt
from django.contrib.auth.hashers import make_password


class TestTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestType
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    sub_category_name = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    class Meta:
        model = Product
        fields = '__all__'

    def get_sub_category_name(self, obj):
        return obj.product_sub_category.sub_category
    
    def get_category_name(self, obj):
        return obj.product_sub_category.product_category.category
    
    def get_customer_name(self, obj):
        return obj.customer.name

class ProductSubCategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    class Meta:
        model = ProductSubCategory
        fields = '__all__'

    def get_product_count(self, obj):
        return obj.product.count()
    
    def get_category_name(self, obj):
        return obj.product_category.category
    
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
