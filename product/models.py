from datetime import datetime, timedelta
from django.db import models
import pytz
from user.query_manager import CustomManager
from user.models import DefaultModel, RequestTracking, User, Customer


class FoundationalModel(DefaultModel, models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=500)
    provider = models.CharField(max_length=255)
    description = models.TextField()
    data = models.JSONField(default={})

    objects = CustomManager()

    def __str__(self) -> str:
        return f"{self.name}"


class TestType(DefaultModel, models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=500)
    description = models.TextField(blank = True, null = True)
    comments = models.TextField(blank = True, null = True)
    last_updated_by = models.CharField(max_length=255)
    executable_codes = models.JSONField(default=dict())

    objects = CustomManager()

    def __str__(self):
        return f"{self.code} - {self.description}"


class TestCategories(DefaultModel, models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    number_of_test_cases = models.IntegerField(blank = True, null = True)
    description = models.TextField(blank = True, null = True)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, related_name = "test_category", on_delete=models.CASCADE, null = True)
    customer = models.ForeignKey(Customer, related_name = "test_category", on_delete=models.CASCADE)
    test_type = models.ForeignKey(TestType, related_name = "test_category", on_delete=models.CASCADE)
    last_updated_by = models.ForeignKey(User, related_name="test_category_last_updated", on_delete=models.CASCADE)
    executable_codes = models.JSONField(default=dict())

    objects = CustomManager()

    def __str__(self) -> str:
        return f"{self.name}-{self.test_type.code}"


class Prompt(DefaultModel, models.Model):
    id = models.AutoField(primary_key=True)
    provider = models.CharField(max_length=255)
    foundation_model = models.CharField(max_length=255)
    rag = models.CharField(max_length=10)
    prompt = models.CharField(max_length=255)
    comments = models.TextField()
    last_updated_by = models.ForeignKey(User, related_name = "prompt", on_delete=models.CASCADE)

    objects = CustomManager()

    def __str__(self):
        return f"{self.provider} - {self.foundation_model} - {self.prompt}"


class ProductCategory(DefaultModel, models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, related_name = "product_category", on_delete=models.CASCADE)
    category = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    last_updated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    prompts = models.ManyToManyField(Prompt, blank=True, related_name = 'product_category', through='ProductCategoryPrompt')

    objects = CustomManager()

    def __str__(self):
        return f"{self.customer.code} - {self.category}"


class ProductSubCategory(DefaultModel, models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, related_name = "product_sub_category", on_delete=models.CASCADE)
    product_category = models.ForeignKey(ProductCategory, related_name = "product_sub_category", on_delete=models.CASCADE)
    sub_category = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    last_updated_by = models.ForeignKey(User, on_delete=models.CASCADE)

    objects = CustomManager()

    def __str__(self):
        return f"{self.customer.code} - {self.product_category.category} - {self.sub_category}"


class ProductCategoryPromptCode(DefaultModel, models.Model):
    id = models.AutoField(primary_key=True)
    product_sub_category = models.ForeignKey(ProductSubCategory, related_name = "product_category_prompt_code", on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, related_name = "product_category_prompt_code",  on_delete=models.CASCADE)
    foundation_model = models.CharField(max_length=255)
    prompt_code = models.CharField(max_length=255)
    comments = models.TextField()
    last_updated_by = models.ForeignKey(User, on_delete=models.CASCADE)

    objects = CustomManager()

    def __str__(self):
        return f"{self.customer.code} - {self.product_sub_category.sub_category} - {self.foundation_model} - {self.prompt_code}"


class Product(DefaultModel, models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, related_name = "product",  on_delete=models.CASCADE)
    product_sub_category = models.ForeignKey(ProductSubCategory, related_name = "product", on_delete=models.CASCADE)
    product_code = models.CharField(max_length=255)
    comments = models.TextField(blank=True, null=True)
    # created_by = models.ForeignKey(User, blank = True, related_name = 'product', on_delete=models.CASCADE)
    last_updated_by = models.ForeignKey(User, related_name = 'product', on_delete=models.CASCADE)
    prompts = models.ManyToManyField(Prompt, blank=True, related_name = 'product', through='ProductPrompt')
    product_name = models.CharField(max_length=255)
    product_category = models.ForeignKey(ProductCategory, related_name = "product", on_delete=models.CASCADE)
    vector_name_space = models.CharField(max_length = 100)

    objects = CustomManager()

    def __str__(self):
        return f"{self.customer.code} - {self.product_sub_category.sub_category} - {self.product_code}"


class ProductCategoryPrompt(DefaultModel, models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, related_name = "product_category_prompt",  on_delete=models.CASCADE)
    product_category = models.ForeignKey(ProductCategory, related_name = "product_category_prompt",  on_delete=models.CASCADE)
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE)
    sequence_no = models.IntegerField()
    executable_prompt = models.CharField(max_length=500)
    comments = models.TextField()
    last_updated_by = models.ForeignKey(User, on_delete=models.CASCADE)

    objects = CustomManager()

    def __str__(self):
        return f"{self.customer.code} - {self.product_category.category} - {self.prompt.prompt} - {self.sequence_no}"


class ProductPrompt(DefaultModel, models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, related_name = "product_prompt",  on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name = "product_prompt", on_delete=models.CASCADE)
    prompt = models.ForeignKey(Prompt, related_name = "product_prompt", on_delete=models.CASCADE)
    sequence_no = models.IntegerField()
    executable_prompt = models.CharField(max_length=500)
    comments = models.TextField()
    last_updated_by = models.ForeignKey(User, on_delete=models.CASCADE)

    objects = CustomManager()

    def __str__(self):
        return f"{self.customer.code} - {self.product.product_code} - {self.prompt.prompt} - {self.sequence_no}"


class TestCases(DefaultModel, models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, related_name = "test_cases",  on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name = "test_cases", on_delete=models.CASCADE)
    test_category = models.ForeignKey(TestCategories, related_name = "test_cases", on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, related_name = 'test_cases', on_delete=models.CASCADE)
    data_url = models.URLField(blank=True, null=True)
    sha = models.CharField(max_length=255, null=True, blank=True)
    data = models.JSONField()
    request = models.ForeignKey(RequestTracking, to_field="request_id", on_delete=models.CASCADE, related_name="test_cases")

    objects = CustomManager()

    def __str__(self):
        return f"{self.product.product_code}-{self.test_type.code}({self.created_at})"
    

class TestScriptExecResults(DefaultModel, models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, related_name="test_script_exec_results", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="test_script_exec_results", on_delete=models.CASCADE)
    test_category = models.ForeignKey(TestCategories, related_name="test_script_exec_results", on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    pass_count = models.IntegerField()
    fail_count = models.IntegerField()
    comments = models.TextField()
    execution_result_details = models.JSONField(default={})
    test_script_number = models.CharField(max_length=255)
    test_type = models.ForeignKey(TestType, related_name="test_script_exec_results", on_delete=models.CASCADE)
    product_sub_category = models.ForeignKey(ProductSubCategory, related_name="test_script_exec_results", on_delete=models.CASCADE)

    objects = CustomManager()

    def __str__(self):
        return f"{self.test_script_number}-{self.product.product_code}({self.created_at})"
    

class StructuredTestCases(DefaultModel, models.Model):
    id = models.AutoField(primary_key=True)
    test_id = models.CharField(max_length=100, null=False, blank=False, db_index=True)
    test_name = models.CharField(max_length=255)
    objective = models.CharField(max_length=500)
    customer = models.ForeignKey(Customer, related_name="structured_test_cases", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="structured_test_cases", on_delete=models.CASCADE)
    data=models.JSONField()
    test_category = models.ForeignKey(TestCategories, related_name="structured_test_cases", on_delete=models.CASCADE, db_index=True)
    test_type = models.ForeignKey(TestType, related_name="structured_test_cases", on_delete=models.CASCADE, db_index=True)
    type = models.CharField(max_length=20)
    request = models.ForeignKey(RequestTracking, to_field="request_id", on_delete=models.CASCADE, related_name="structured_test_cases", db_index=True)
    created_by = models.ForeignKey(User, related_name="structured_test_cases", on_delete=models.CASCADE)

    objects = CustomManager()

    def save(self,*args, **kwargs):
        self.test_type = self.test_category.test_type
        return super().save()
    
    def __str__(self):
        return f"{self.test_id}"


class KnowledgeBasePrompts(DefaultModel, models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, related_name="knowledge_base_prompts", on_delete=models.CASCADE)
    test_category = models.ForeignKey(TestCategories, related_name="knowledge_base_prompts", on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, related_name="knowledge_base_prompts_created_by", on_delete=models.CASCADE)
    updated_by = models.ForeignKey(User, related_name="knowledge_base_prompts_updated_by", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=500)
    description = models.TextField(blank = True, null = True)
    sequence_no = models.IntegerField()
    top_k = models.IntegerField()
    query = models.TextField()
    default_data = models.TextField()

    objects = CustomManager()

    def __str__(self):
        return self.name



class KnowledgeBaseResults(DefaultModel, models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, related_name="knowledge_base_results", on_delete=models.CASCADE)
    kb_prompt = models.ForeignKey(KnowledgeBasePrompts, related_name="knowledge_base_results", on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, related_name="knowledge_base_results_created_by", on_delete=models.CASCADE)
    # updated_by = models.ForeignKey(User, related_name="knowledge_base_results_updated_by", on_delete=models.CASCADE)
    request = models.ForeignKey(RequestTracking, to_field='request_id', related_name="knowledge_base_results", on_delete=models.CASCADE)
    query = models.TextField()
    top_k_docs = models.JSONField()
    summary_of_docs = models.TextField()

    objects = CustomManager()

    def __str__(self):
        return self.query

