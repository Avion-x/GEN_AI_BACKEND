from django.db import models
from product.query_manager import CustomManager
from user.models import User, Customer


class FoundationalModel(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=500)
    provider = models.CharField(max_length=255)
    description = models.TextField()
    status = models.BooleanField(default=True)
    valid_till = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    data = models.JSONField(default={})

    def __str__(self) -> str:
        return f"{self.name}"

class TestType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=500)
    description = models.TextField()
    status = models.BooleanField()
    valid_till = models.DateField(null=True, blank=True)
    comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    last_updated_by = models.CharField(max_length=255)
    executable_codes = models.JSONField(default=dict())

    def __str__(self):
        return f"{self.code} - {self.description}"
    
class TestCategories(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    number_of_test_cases = models.IntegerField()
    description = models.TextField()
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, related_name = "test_category", on_delete=models.CASCADE)
    status = models.BooleanField()
    valid_till = models.DateField(null=True, blank=True)
    customer = models.ForeignKey(Customer, related_name = "test_category", on_delete=models.CASCADE)
    test_type = models.ForeignKey(TestType, related_name = "test_category", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    last_updated_by = models.CharField(max_length=255)
    executable_codes = models.JSONField(default=dict())

    def __str__(self) -> str:
        return f"{self.name}-{self.test_type.code}"

class Prompt(models.Model):
    id = models.AutoField(primary_key=True)
    provider = models.CharField(max_length=255)
    foundation_model = models.CharField(max_length=255)
    rag = models.CharField(max_length=10)
    prompt = models.CharField(max_length=255)
    status = models.BooleanField()
    valid_till = models.DateField(null=True, blank=True)
    comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(User, related_name = "prompt", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.provider} - {self.foundation_model} - {self.prompt}"


class ProductCategory(models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, related_name = "product_category", on_delete=models.CASCADE)
    category = models.CharField(max_length=255)
    description = models.TextField()
    status = models.BooleanField()
    valid_till = models.DateField(null=True, blank=True)
    comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    prompts = models.ManyToManyField(Prompt, blank=True, related_name = 'product_category', through='ProductCategoryPrompt')

    # objects = CustomManager()

    def __str__(self):
        return f"{self.customer.code} - {self.category}"
    
class ProductSubCategory(models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, related_name = "product_sub_category", on_delete=models.CASCADE)
    product_category = models.ForeignKey(ProductCategory, related_name = "product_sub_category", on_delete=models.CASCADE)
    sub_category = models.CharField(max_length=255)
    description = models.TextField()
    status = models.BooleanField()
    valid_till = models.DateField(null=True, blank=True)
    comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.customer.code} - {self.product_category.category} - {self.sub_category}"
    
class ProductCategoryPromptCode(models.Model):
    id = models.AutoField(primary_key=True)
    product_sub_category = models.ForeignKey(ProductSubCategory, related_name = "product_category_prompt_code", on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, related_name = "product_category_prompt_code",  on_delete=models.CASCADE)
    foundation_model = models.CharField(max_length=255)
    prompt_code = models.CharField(max_length=255)
    status = models.BooleanField()
    valid_till = models.DateField(null=True, blank=True)
    comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.customer.code} - {self.product_sub_category.sub_category} - {self.foundation_model} - {self.prompt_code}"
    
class Product(models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, related_name = "product",  on_delete=models.CASCADE)
    product_sub_category = models.ForeignKey(ProductSubCategory, related_name = "product", on_delete=models.CASCADE)
    product_code = models.CharField(max_length=255)
    status = models.BooleanField()
    valid_till = models.DateField(null=True, blank=True)
    comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, blank = True, related_name = 'product', on_delete=models.CASCADE)
    last_updated_by = models.ForeignKey(User, related_name = 'product', on_delete=models.CASCADE)
    prompts = models.ManyToManyField(Prompt, blank=True, related_name = 'product', through='ProductPrompt')

    def __str__(self):
        return f"{self.customer.code} - {self.product_sub_category.sub_category} - {self.product_code}"

class ProductCategoryPrompt(models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, related_name = "product_category_prompt",  on_delete=models.CASCADE)
    product_category = models.ForeignKey(ProductCategory, related_name = "product_category_prompt",  on_delete=models.CASCADE)
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE)
    sequence_no = models.IntegerField()
    executable_prompt = models.CharField(max_length=500)
    status = models.BooleanField()
    valid_till = models.DateField(null=True, blank=True)
    comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.customer.code} - {self.product_category.category} - {self.prompt.prompt} - {self.sequence_no}"

class ProductPrompt(models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, related_name = "product_prompt",  on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name = "product_prompt", on_delete=models.CASCADE)
    prompt = models.ForeignKey(Prompt, related_name = "product_prompt", on_delete=models.CASCADE)
    sequence_no = models.IntegerField()
    executable_prompt = models.CharField(max_length=500)
    status = models.BooleanField()
    valid_till = models.DateField(null=True, blank=True)
    comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.customer.code} - {self.product.product_code} - {self.prompt.prompt} - {self.sequence_no}"



class TestCases(models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, related_name = "test_cases",  on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name = "test_cases", on_delete=models.CASCADE)
    test_type = models.ForeignKey(TestType, related_name = "test_cases", on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, related_name = 'test_cases', on_delete=models.CASCADE)
    data_url = models.URLField(blank=True, null=True)
    sha = models.CharField(max_length=255, null=True, blank=True)
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.product_code}-{self.test_type.code}({self.created_at})"
    