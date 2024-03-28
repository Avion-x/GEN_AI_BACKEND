

import os
import json
import boto3
from datetime import datetime
from event_manager.service.cronjob_registry import CronJobRegistry
from event_manager.models import CronExecution

PENDING_STATUS = 'PENDING'
EXECUTING_STATUS = 'EXECUTING'
SUCCESS_STATUS = 'SUCCESS'
FAILED_STATUS = 'FAILED'

class CronJob(CronJobRegistry):
    def __init__(self):
        super().__init__()

    def performOperation(self):
        job = {}
        try:
            cronjobs = self.getPendingCronjobs()
            for job in cronjobs:
                self.executeCronJob(job)
        except Exception as e:
            self.handleException(job, e)

    def getPendingCronjobs(self):
        cronjobs = CronExecution.objects.filter(pickup_time__lte=datetime.now(), is_executable=True, execution_status=PENDING_STATUS)
        return cronjobs

    def executeCronJob(self, job_data):
        try:
            cron_job_name = job_data.name
            if not cron_job_name:
                raise Exception('CronJobName not specified')
            cronFucntion = self.registry.get(cron_job_name, None)
            if not cronFucntion:
                raise Exception('CronJobName is incorrect')
            result = cronFucntion(job_data.params)
            self.update_status_in_db(job_data, result)
        except Exception as e:
            raise e

    def update_status_in_db(self, job_data, result):
        try:
            result = self.processResult(result)
            status = result.get('status').upper()
            result = json.dumps(result).replace("'", '')
            if status != PENDING_STATUS:
                job_data.execution_status = status
                job_data.result = result
                job_data.is_executable=False
                job_data.save()
            return True
        except Exception as e:
            print(f"unable to update db with job_data \n{job_data}\n Exception: {e}")

    def processResult(self, result):
        if isinstance(result, dict):
            return result
        else:
            return {
                "status": SUCCESS_STATUS if result else FAILED_STATUS
            }

    def handleException(self, job_data, exception):
        exception_data = {
            "status": FAILED_STATUS,
            "message": str(exception)
        }
        self.update_status_in_db(job_data, exception_data)
