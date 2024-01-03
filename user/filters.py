import django_filters
from rest_framework import filters
from user.models import User

class CustomUserFilter(django_filters.FilterSet):
    username = django_filters.CharFilter(lookup_expr='icontains')
    email = django_filters.CharFilter(lookup_expr='icontains')
    id = django_filters.NumberFilter(lookup_expr='exact')
    from_date = django_filters.DateFilter(field_name='date_joined', lookup_expr='gte')
    to_date = django_filters.DateFilter(field_name='date_joined', lookup_expr='lte')

    ordering_fields = ['username', 'created_at', 'updated_at']
    class Meta:
        model = User
        fields = ['username', 'email', 'id', 'from_date', 'to_date']
        # fields = '__all__'


    # filterset_fields = ['username', 'id', 'email']
    # search_fields = ['username', 'email'] #for search filters
    # filterset_fields = {
    #     'created_at': ['gte', 'lte', 'exact', 'gt', 'lt'],
    #     'updated_at' : ['gte', 'lte', 'exact', 'gt', 'lt'],
    #     'id' : ['exact']
    # }
    # 
    # 