

from django.db.models import Manager, QuerySet



class CustomManager(Manager):

    def get_queryset(self) -> QuerySet:
        return super().get_queryset(customer_id=self.request.user.customer_id)