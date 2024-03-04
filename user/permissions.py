from django.contrib.auth.models import User, Permission
from .models import Roles
import json

def get_user_permissions(username):
    user_permissions = (
        Permission.objects
        .filter(group__roles__group__user__username=username)
        .values_list('name', flat=True)
        .distinct()
    )
    permissions_json = json.dumps(list(user_permissions))
    return permissions_json