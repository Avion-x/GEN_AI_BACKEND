
from datetime import date
from django.db import models
from django.db.models import Manager, QuerySet



class CustomManagerException(Exception):
    def __init__(self, message=None, code=None, params=None):
        super().__init__(message, code, params)

class CustomManager(Manager):
    def get_queryset(self):
        try:
            """
            Override get_queryset to filter tenants based on the tenant associated with the login user.
            """
            from user.middleware.request_tracking_middleware import get_current_request
            request = get_current_request()
            if request and request.user.is_authenticated:
                filters = {
                    "valid_till__gt" : date.today(),
                    "status" : True,
                }
                if hasattr(self.model, "customer"):
                    if request.user.customer.code == "AvionX":
                        from user.models import Customer
                        filters["customer_id__in"] = list(Customer.objects.values_list('id', flat=True))
                    else:
                        filters["customer"] = request.user.customer
                return super().get_queryset().filter(**filters)
            else:
                return super().get_queryset().none()
        except CustomManagerException as e:
            raise CustomManagerException(message=f"Request Not Found to filter customer, Error is {e}")
        
    def get_default_queryset(self):
        try:
            super().get_queryset()
        except Exception as e:
            raise e
        
class UserManager(Manager):

    def get_by_natural_key(self, username):
        return self.get(username=username)
    
    def get_queryset(self) -> QuerySet:
        try:
            """
            Override get_queryset to filter tenants based on the tenant associated with the login user.
            """
            from user.middleware.request_tracking_middleware import get_current_request

            request = get_current_request()
            if request and request.user.is_authenticated:
                filters = {
                    "valid_till__gt" : date.today(),
                    "status" : True,
                }
                if hasattr(self.model, "customer"):
                    if request.user.customer.code == "AvionX":
                        from user.models import Customer
                        filters["customer_id__in"] = list(Customer.objects.values_list('id', flat=True))
                    else:
                        filters["customer"] = request.user.customer
                return super().get_queryset().filter(**filters)
            else:
                return super().get_queryset()
        except CustomManagerException as e:
            raise CustomManagerException(message=f"Request Not Found to filter customer, Error is {e}")