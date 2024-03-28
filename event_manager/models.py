from django.db import models
from user.models import DefaultModel, RequestTracking, User, Customer
from user.query_manager import CustomManager
from datetime import datetime

# Create your models here.

# class CronJob(DefaultModel, models.Model):
#     id = models.AutoField(primary_key=True)
#     name = models.CharField(max_length=20)
#     is_executable = models.BooleanField(default=True)
    
#     def __str__(self):
#         return self.name
    


class CronExecution(DefaultModel, models.Model):
    status_choices = (
        ('PENDING', 'PENDING'),
        ('EXECUTING', 'EXECUTING'),
        ('SUCCESS', 'SUCCESS'),
        ('FAILED', 'FAILED')
    )
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    pickup_time = models.DateTimeField(default=datetime.now())
    is_executable = models.BooleanField(default=True)
    execution_status = models.CharField(max_length=15, default="PENDING", choices=status_choices)
    customer = models.ForeignKey(Customer, related_name="cron_execution", on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, related_name="cron_execution", on_delete=models.CASCADE)
    request = models.ForeignKey(RequestTracking, to_field='request_id', related_name="cron_execution", on_delete=models.CASCADE)
    params = models.JSONField(default=dict)
    results = models.JSONField(default=dict)

    def __str__(self):
        return self.name
    