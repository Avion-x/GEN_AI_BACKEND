from django.urls import path, include
from django.contrib import admin

from .views import (UserView, LoginView, LogoutView, CreateRoleWithGroupsAPIView)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('create_role_group/', CreateRoleWithGroupsAPIView.as_view(), name='role-create'),
    path('users/', UserView.as_view(), name='user-list-create'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('product/', include('product.urls')),
]


