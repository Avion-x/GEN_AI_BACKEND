from django.urls import path, include
from django.contrib import admin

from .views import (UserView, LoginView, LogoutView, CustomerOrEnterpriseView, CheckUsernameExistsView, CreateRoleWithGroupsAPIView, CheckEmailExistsView)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('create_role_group/', CreateRoleWithGroupsAPIView.as_view(), name='role-create'),
    path('users/', UserView.as_view(), name='user-list-create'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('product/', include('product.urls')),
    path('customers/', CustomerOrEnterpriseView.as_view(), name='customers'),
    path('check_username/', CheckUsernameExistsView.as_view(), name='check-username'),
    path('check_email/', CheckEmailExistsView.as_view(), name='check-email'),
]


