from django.urls import path
from django.contrib import admin
from .views import LatestTestTypesWithCategoriesOfProduct, TestCasesAndScripts, TestResponse, TestSubCategoryParameters, TestTypeView, ProductCategoryView, \
    ProductSubCategoryView, ProductView, GenerateTestCases, TestCasesView, GetFileCommitsView, GetFileChangesView, \
    GetFilesInCommitView, TestCategoriesView, TestScriptExecResultsView, GeneratedTestCategoriesView, DashboardKpi, \
    PendingApprovalTestCategoryView, ApproveTestCategoryView, DashboardChart, ExtractTextFromPDFView, \
    CategoryDetailsView, UploadDeviceDocsView, EmbedUploadedDocs, UserCreatedTestCasesAndScripts, TestSubCategoriesView
    
urlpatterns = [
    path('admin/', admin.site.urls),
    path('testtypes/', TestTypeView.as_view(), name='test-type'),
    path('productcategory/', ProductCategoryView.as_view(), name='product-category'),
    path('productsubcategory/', ProductSubCategoryView.as_view(), name='product-sub-category'),
    path('product/', ProductView.as_view(), name='product'),
    path("generate_test_cases/", GenerateTestCases.as_view(), name='generate-test-cases'),
    path("structured_test_cases_and_scripts/", TestCasesAndScripts.as_view(), name='structured_test_cases_and_scripts'),
    path("user_created_test_cases_and_scripts/", UserCreatedTestCasesAndScripts.as_view(), name='user_created_test_cases_and_scripts'),
    path('latest_test_types_with_categories/', LatestTestTypesWithCategoriesOfProduct.as_view(),
         name='latest_test_types_with_categories'),
    path('test_cases/', TestCasesView.as_view(), name='test_cases'),
    path('file_commits/', GetFileCommitsView.as_view(), name='file_commits'),
    path('file_changes/', GetFileChangesView.as_view(), name='file_changes'),
    path('files_in_commit/', GetFilesInCommitView.as_view(), name='files_in_commit'),
    path('test_categories/', TestCategoriesView.as_view(), name='test_categories'),
    path('test_execution/', TestScriptExecResultsView.as_view(), name='test_execution'),
    path('generated_categories/', GeneratedTestCategoriesView.as_view(), name='generated_categories'),
    path('dashboard_kpi/', DashboardKpi().as_view(), name='dashboard_kpi'),
    path('pending_approval_test_categories/', PendingApprovalTestCategoryView.as_view(),
         name='pending_approval_test_categories'),
    path('approve_test_category/', ApproveTestCategoryView.as_view(), name='approve_test_category'),
    path('dashboard_chart/', DashboardChart().as_view(), name='dashboard_chart'),
    path('upload_device_docs/', UploadDeviceDocsView.as_view(), name = "upload_device_docs"),
    path('extract_pdf/', ExtractTextFromPDFView.as_view(), name='extract_pdf'),
    path('category_details/', CategoryDetailsView.as_view(), name='category_details'),
    path('embed_uploaded_docs/', EmbedUploadedDocs.as_view(), name='embed_uploaded_docs'),
    path('test_sub_categories/', TestSubCategoriesView.as_view(), name='test_sub_categories'),
    path('demo_reply', TestResponse.as_view(), name='demo_reply'),
    path('get_test_sub_category_params/', TestSubCategoryParameters.as_view(), name='get_test_sub_category_params')

]


