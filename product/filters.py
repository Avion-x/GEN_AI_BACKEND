import django_filters
from django.db import models
from rest_framework import filters
from .models import StructuredTestCases, TestType, ProductCategory, Product, ProductCategoryPrompt, ProductCategoryPromptCode, ProductPrompt, \
    ProductSubCategory, Prompt, TestCases, TestCategories, TestScriptExecResults, TestSubCategories


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


class LatestTestTypesWithCategoriesOfProductFilter(django_filters.FilterSet):
    product_id = django_filters.NumberFilter(lookup_expr='exact')
    created_by_id = django_filters.NumberFilter(lookup_expr='exact')

    class Meta:
        model = StructuredTestCases
        fields = '__all__'
        filter_overrides = {
            models.JSONField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'exact',
                },
            },
        }


class TestCasesFilter(django_filters.FilterSet):
    product_id = django_filters.NumberFilter(lookup_expr='exact')
    created_by_id = django_filters.NumberFilter(lookup_expr='exact')

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
    test_type_id = django_filters.NumberFilter(lookup_expr='exact')

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


class PromptFilter(django_filters.FilterSet):
    id = django_filters.NumberFilter(lookup_expr='exact')
    prompt = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Prompt
        fields = ['id', 'prompt']


class TestExecutionResultsFilter(django_filters.FilterSet):
    test_script_number = django_filters.NumberFilter(lookup_expr='exact')

    class Meta:
        model = TestScriptExecResults
        fields = ['id', 'test_script_number', 'created_by']
        filter_overrides = {
            models.JSONField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'exact',
                },
            },
        }


class TestSubCategoriesFilter(django_filters.FilterSet):
    test_type_id = django_filters.NumberFilter(lookup_expr='exact')

    class Meta:
        model = TestSubCategories
        fields = '__all__'
        filter_overrides = {
            models.JSONField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'exact',
                },
            },
        }