from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from .models import RouterDetails

EQUALS = ""
CONTAINS = "__contains"
ICONTAINS = "__icontains"

def show_routers(request):
    filters = get_router_filters(request, registry = {
        "router_id" : {
            "db_field" : "id",
            "search" : EQUALS
        },
        "parent_id" : {
            "db_field" : "parent_id",
            "search" : EQUALS
        },
        "router_name" : {
            "db_field" : "name",
            "search" : ICONTAINS
        },
        "router_model" : {
            "db_field" : "model_no",
            "search" : ICONTAINS
        }
    })
    if not filters:
        filters['parent__isnull'] = True
    routers = RouterDetails.objects.filter(**filters).all()
    return render(request, 'router_details.html', {'routers': list(routers)})

def get_router_filters(request, registry={}):
    filters = {}
    for key, value in request.GET.items():
        if registry.get(key):
            filters[f"{registry[key]['db_field']}{registry[key]['search']}"] = value
    return filters


def show_routers_tree(request):
    filters = {'parent__isnull' : True} or get_router_filters(request, registry = {
        "router_id" : {
            "db_field" : "id",
            "search" : EQUALS
        },
        "parent_id" : {
            "db_field" : "parent_id",
            "search" : EQUALS
        },
        "router_name" : {
            "db_field" : "name",
            "search" : ICONTAINS
        },
        "router_model" : {
            "db_field" : "model_no",
            "search" : ICONTAINS
        }
    })
    routers = RouterDetails.objects.filter(**filters).all()

    routers_data = []
    for router in routers:
        router_data = {
            'id': router.id,
            'name': router.name,
            'model_no': router.model_no,
            'maker_name': router.maker_name,
            'is_leaf': router.is_leaf,
            'children': get_child_data(router),
        }
        routers_data.append(router_data)
    print(routers_data)
    return render(request, 'router_tree.html', {'routers': routers_data})


def get_child_data(router):
    # Base case: If the router is a leaf node, return an empty dictionary
    if router.is_leaf:
        return {}

    # Recursive case: Get child data for each child router
    children_data = {}
    for child in router.routerdetails_set.all():
        children_data[child.id] = {
            'name': child.name,
            'model_no': child.model_no,
            'maker_name': child.maker_name,
            'is_leaf': child.is_leaf,
            'children': get_child_data(child),  # Recursively get child data
        }

    return children_data