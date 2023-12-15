from django.db import models
from django.contrib.auth.models import AbstractUser


class Customer(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    address = models.TextField()
    status = models.BooleanField(max_length=50)
    valid_till = models.DateField(null=True, blank=True)
    comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    last_updated_by = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.code} - {self.name}"
    
class CustomerConfig(models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.OneToOneField(Customer, related_name = "customer_config", on_delete=models.CASCADE)
    config_type = models.CharField(max_length=255)
    config_value = models.CharField(max_length=255)
    status = models.BooleanField(max_length=50)
    valid_till = models.DateField(null=True, blank=True)
    comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    last_updated_by = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.customer.code} - {self.config_type}"
    
class AccessType(models.Model):
    id = models.AutoField(primary_key=True)
    access = models.CharField(max_length=255)
    description = models.TextField()
    status = models.BooleanField()
    valid_till = models.DateField(null=True, blank=True)
    comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    last_updated_by = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.access} - {self.description}"

class User(AbstractUser):
    customer = models.ForeignKey(Customer, related_name = "user", on_delete=models.CASCADE, default=1)
    valid_till = models.DateField(null=True, blank=True)
    comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True),
    last_updated_at = models.DateTimeField(auto_now=True)
    last_updated_by = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.customer.code} - {self.username}"

class UserAccess(models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, related_name = "user_access", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    access_type = models.ForeignKey(AccessType, on_delete=models.CASCADE)
    status = models.BooleanField()
    valid_till = models.DateField(null=True, blank=True)
    comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    last_updated_by = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.customer.code} - {self.user.username} - {self.access_type.access}"


class RouterDetails(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    model_no = models.CharField(max_length=50)
    maker_name = models.CharField(max_length=100)
    is_leaf = models.BooleanField(default=False)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name


