from django.urls import path, include
from django.contrib import admin

from .views import (UserView, LoginView, LogoutView, CustomerOrEnterpriseView, CheckUsernameExistsView)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', UserView.as_view(), name='user-list-create'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('product/', include('product.urls')),
    path('customers/', CustomerOrEnterpriseView.as_view(), name='customers'),
    path('check_username/', CheckUsernameExistsView.as_view(), name='check-username'),
]


