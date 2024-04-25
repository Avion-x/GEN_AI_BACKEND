

import os
import json
import boto3
from datetime import datetime
from event_manager.service.cronjob_registry import CronJobRegistry
from event_manager.models import CronExecution
from product.services.generic_services import rebuild_request
from user.middleware.request_tracking_middleware import set_current_request, delete_current_request

PENDING_STATUS = 'PENDING'
EXECUTING_STATUS = 'EXECUTING'
SUCCESS_STATUS = 'SUCCESS'
FAILED_STATUS = 'FAILED'

class CronJob(CronJobRegistry):
    def __init__(self):
        super().__init__()

    def performOperation(self):
        self.job_data = {}
        try:
            cronjobs = self.getPendingCronjobs()
            for job in cronjobs:
                self.job_data = job
                self.executeCronJob()
        except Exception as e:
            self.handleException(e)

    def getPendingCronjobs(self):
        cronjobs = CronExecution.objects.filter(pickup_time__lte=datetime.now(), is_executable=True, execution_status=PENDING_STATUS)
        return cronjobs

    def executeCronJob(self):
        try:
            cron_job_name = self.job_data.name
            if not cron_job_name:
                raise Exception('CronJobName not specified')
            cronFucntion = self.registry.get(cron_job_name, None)
            if not cronFucntion:
                raise Exception('CronJobName is incorrect')
            self.request = rebuild_request(self.job_data.request.request_id)
            set_current_request(self.request)
            result = cronFucntion(self.job_data.params, self.request)
            self.update_status_in_db(result)
            delete_current_request()
        except Exception as e:
            raise e

    def update_status_in_db(self, result):
        try:
            result = self.processResult(result)
            status = result.get('status').upper()
            # result = json.dumps(result).replace("'", '')
            if status != PENDING_STATUS:
                self.job_data.execution_status = status
                self.job_data.results = result
                self.job_data.is_executable=False
            self.job_data.save()
            return True
        except Exception as e:
            print(f"unable to update db with self.job_data \n{self.job_data}\n Exception: {e}")

    def processResult(self, result):
        if isinstance(result, dict):
            return result
        else:
            return {
                "status": SUCCESS_STATUS if result else FAILED_STATUS
            }

    def handleException(self, exception):
        exception_data = {
            "status": FAILED_STATUS,
            "message": str(exception)
        }
        self.update_status_in_db(exception_data)



def run():
    try:
        a = CronJob()
        a.performOperation()
    except Exception as e:
        print("Exception in calling cronjob: ", e)
        raise e
