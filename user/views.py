from rest_framework import generics
from rest_framework.response import Response
from .models import User, Customer, CustomerConfig, AccessType
from product.models import TestType
from .serializers import UserRetriveSerializer, UserSerializer, CustomerSerializer, CustomerConfigSerializer, TestTypeSerializer, AccessTypeSerializer


class UserView(generics.ListCreateAPIView,generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = UserRetriveSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)

    def put(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=204)

