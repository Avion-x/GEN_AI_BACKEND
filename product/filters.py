import django_filters
from django.db import models
from rest_framework import filters
from .models import TestType, ProductCategory, Product, ProductCategoryPrompt, ProductCategoryPromptCode, ProductPrompt, ProductSubCategory, Prompt, TestCases, TestCategories

class TestTypeFilter(django_filters.FilterSet):

    id = django_filters.NumberFilter(lookup_expr='exact')
    code = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = TestType
        fields = ['id', 'code']

class ProductCategoryFilter(django_filters.FilterSet):

    id = django_filters.NumberFilter(lookup_expr='exact')
    category = django_filters.CharFilter(lookup_expr='icontains')
    status = django_filters.BooleanFilter()
    valid_till = django_filters.DateFilter()

    class Meta:
        model = ProductCategory
        fields = ['id', 'category', 'status', 'valid_till']

class ProductSubCategoryFilter(django_filters.FilterSet):

    id = django_filters.NumberFilter(lookup_expr='exact')
    sub_category = django_filters.CharFilter(lookup_expr='icontains')
    product_category = django_filters.NumberFilter(lookup_expr='exact')
    status = django_filters.BooleanFilter()
    valid_till = django_filters.DateFilter()

    class Meta:
        model = ProductSubCategory
        fields = ['id', 'sub_category', 'product_category', 'status', 'valid_till']

class ProductFilter(django_filters.FilterSet):

    id = django_filters.NumberFilter(lookup_expr='exact')
    product_code = django_filters.CharFilter(lookup_expr='icontains')
    product_sub_category = django_filters.NumberFilter(lookup_expr='exact')
    status = django_filters.BooleanFilter()
    valid_till = django_filters.DateFilter()

    class Meta:
        model = Product
        fields = ['id', 'product_code', 'product_sub_category', 'status', 'valid_till']

class TestCasesFilter(django_filters.FilterSet):
    class Meta:
        model = TestCases
        fields = '__all__'
        filter_overrides = {
            models.JSONField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'exact',
                },
            },
        }

class TestCategoriesFilter(django_filters.FilterSet):

    class Meta:
        model = TestCategories
        fields = '__all__'
        filter_overrides = {
            models.JSONField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'exact',
                },
            },
        }
