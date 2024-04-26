

import os
import json
import boto3
from datetime import datetime
from product.models import Product

from product.services.generate_tests import GenerateTests
from product.services.lammaindex import VectorStoreService
from product.services.generic_services import delete_local_directory, download_files_from_s3, extract_pdf

PENDING = 'PENDING'
EXECUTING = 'EXECUTING'
SUCCESS = 'SUCCESS'
FAILED = 'FAILED'

PENDING_STATUS = 'PENDING'
EXECUTING_STATUS = 'EXECUTING'
SUCCESS_STATUS = 'SUCCESS'
FAILED_STATUS = 'FAILED'


class CronJobRegistry():
    def __init__(self):
        self.registry = {
            "CREATE_VECTOR_EMBEDDINGS": self.create_vector_embeddings,
            "GENERATE_TEST_CASES" : self.generate_test_cases
        }

    def generate_test_cases(self, job_data, request, *args, **kwargs):
        try:
            generate_test = GenerateTests(request, **job_data)
            result = generate_test.process_request()
            return {
                "status": SUCCESS_STATUS,
                "message" : "Test cases generated successfully.",
                "result" : result
            }
        except Exception as e:
            raise e

    def create_vector_embeddings(self, job_data, reqeust, *args, **kwargs):
        try:
            product_id = job_data.get('device_id',None) or job_data.params.get('product_id', None)
            
            product = Product.objects.filter(id=product_id).first()
            if not product:
                raise Exception(f"Please pass valid device_id in input_params. Passed {product_id}")
            
            bucket_name = 'genaidev'
            key_prefix = f'devices/{product.product_code}/'

            extract_pdf(bucket_name=bucket_name, folder_path=key_prefix)

            local_directory = os.path.join(os.getcwd(), 'data', product.product_code)
            download_files_from_s3(bucket_name, key_prefix+'processed/', local_directory)

            job_data['pinecone_namespace'] = product.pinecone_name_space
            job_data['data_dir'] = local_directory
            vector_store_service = VectorStoreService(**job_data)
            result = vector_store_service.execute()
            delete_local_directory(local_directory)
            return {
                "status": SUCCESS_STATUS,
                "message": f"Created vector embeddings successfully for the device {product.product_code} in pinecone namespace {product.pinecone_name_space}."
            }
        except Exception as e:
            raise e
