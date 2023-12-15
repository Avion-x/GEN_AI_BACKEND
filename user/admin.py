from django.contrib import admin
from .models import User, Customer, CustomerConfig, AccessType, UserAccess

from product.models import ProductCategory, TestType, ProductSubCategory, ProductCategoryPromptCode, Prompt, Product, ProductCategoryPrompt, ProductPrompt

admin.site.register(User)
admin.site.register(UserAccess)
admin.site.register(Customer)
admin.site.register(CustomerConfig)
admin.site.register(TestType)
admin.site.register(AccessType)
admin.site.register(ProductCategory)
admin.site.register(ProductSubCategory)
admin.site.register(ProductCategoryPromptCode)
admin.site.register(Prompt)
admin.site.register(Product)
admin.site.register(ProductCategoryPrompt)
admin.site.register(ProductPrompt)

