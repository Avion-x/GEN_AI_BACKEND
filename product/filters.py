import django_filters
from rest_framework import filters
from .models import TestType, ProductCategory, Product, ProductCategoryPrompt, ProductCategoryPromptCode, ProductPrompt, ProductSubCategory, Prompt

class TestTypeFilter(django_filters.FilterSet):

    id = django_filters.NumberFilter(lookup_expr='exact')
    code = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = TestType
        fields = ['id', 'code']

class ProductCategoryFilter(django_filters.FilterSet):

    id = django_filters.NumberFilter(lookup_expr='exact')
    category = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = ProductCategory
        fields = ['id', 'category']

class ProductSubCategoryFilter(django_filters.FilterSet):

    id = django_filters.NumberFilter(lookup_expr='exact')
    sub_category = django_filters.CharFilter(lookup_expr='icontains')
    product_category = django_filters.NumberFilter(lookup_expr='exact')

    class Meta:
        model = ProductSubCategory
        fields = ['id', 'sub_category', 'product_category']

class ProductFilter(django_filters.FilterSet):

    id = django_filters.NumberFilter(lookup_expr='exact')
    product_code = django_filters.CharFilter(lookup_expr='icontains')
    product_sub_category = django_filters.NumberFilter(lookup_expr='exact')

    class Meta:
        model = Product
        fields = ['id', 'product_code', 'product_sub_category']
