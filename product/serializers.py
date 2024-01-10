from rest_framework import serializers
from .models import TestType, ProductCategory, Product, ProductCategoryPrompt, ProductCategoryPromptCode, ProductPrompt, ProductSubCategory, Prompt
from product.models import TestType
from django.contrib.auth.hashers import make_password


class TestTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestType
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Product
        fields = '__all__'

class ProductSubCategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    class Meta:
        model = ProductSubCategory
        fields = '__all__'

    def get_product_count(self, obj):
        return obj.product.count()

class ProductCategorySerializer(serializers.ModelSerializer):
    sub_category_count = serializers.SerializerMethodField()
    class Meta:
        model = ProductCategory
        # fields = '__all__'
        exclude = ['prompts']

    def get_sub_category_count(self, obj):
        return obj.product_sub_category.count()
