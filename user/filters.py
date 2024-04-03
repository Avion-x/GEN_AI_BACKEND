import django_filters
from rest_framework import filters
from user.models import User, Customer

class CustomUserFilter(django_filters.FilterSet):
    username = django_filters.CharFilter(lookup_expr='icontains')
    email = django_filters.CharFilter(lookup_expr='icontains')
    id = django_filters.NumberFilter(lookup_expr='exact')
    from_date = django_filters.DateFilter(field_name='date_joined', lookup_expr='gte')
    to_date = django_filters.DateFilter(field_name='date_joined', lookup_expr='lte')
    class Meta:
        model = User
        fields = ['username', 'email', 'id', 'from_date', 'to_date']


class CustomerFilter(django_filters.FilterSet):
    id = django_filters.NumberFilter(lookup_expr='exact')

    class Meta:
        model = Customer
        fields = '__all__'
        