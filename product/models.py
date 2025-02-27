from django.db import models
from user.models import User, Customer



class TestType(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=255)
    description = models.TextField()
    status = models.BooleanField()
    valid_till = models.DateField(null=True, blank=True)
    comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    last_updated_by = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.code} - {self.description}"

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
    last_updated_by = models.ForeignKey(User, on_delete=models.CASCADE)

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
    last_updated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    prompts = models.ManyToManyField(Prompt, blank=True, related_name = 'product', through='ProductPrompt')

    def __str__(self):
        return f"{self.customer.code} - {self.product_sub_category.sub_category} - {self.product_code}"

class ProductCategoryPrompt(models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, related_name = "product_category_prompt",  on_delete=models.CASCADE)
    product_category = models.ForeignKey(ProductCategory, related_name = "product_category_prompt",  on_delete=models.CASCADE)
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE)
    sequence_no = models.IntegerField()
    executable_prompt = models.BooleanField()
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
    executable_prompt = models.BooleanField()
    status = models.BooleanField()
    valid_till = models.DateField(null=True, blank=True)
    comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.customer.code} - {self.product.product_code} - {self.prompt.prompt} - {self.sequence_no}"

