from django.contrib.auth.models import Group, Permission
from .models import Roles, User
import json

def get_user_permissions(username):
    # Retrieve user object
    user = User.objects.get(username=username)

    # Retrieve user's roles
    user_roles = Role.objects.filter(group__user=user)

    # Retrieve groups associated with the user's roles
    user_groups = Group.objects.filter(role__in=user_roles)

    # Retrieve permissions associated with the user's roles and groups
    permissions = Permission.objects.filter(group__in=user_groups)

    # Extract permission names
    permission_names = [permission.name for permission in permissions]

    # Serialize permissions to JSON
    permissions_json = json.dumps(permission_names)

    return permissions_json
