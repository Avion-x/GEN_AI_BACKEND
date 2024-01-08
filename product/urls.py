from django.urls import path
from django.contrib import admin
from .views import TestTypeView, ProductCategoryView, ProductSubCategoryView, ProductView, FileUploadView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('testtypes/', TestTypeView.as_view(), name='test-type'),
    path('productcategory/', ProductCategoryView.as_view(), name='product-category'),
    path('productsubcategory/', ProductSubCategoryView.as_view(), name='product-sub-category'),
    path('product/', ProductView.as_view(), name='product'),
    path('upload/', FileUploadView.as_view(), name='file_upload'),
]