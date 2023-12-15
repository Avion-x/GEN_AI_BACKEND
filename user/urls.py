from django.urls import path
from django.contrib import admin

from .views import ( UserView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', UserView.as_view(), name='user-list-create'),
]
