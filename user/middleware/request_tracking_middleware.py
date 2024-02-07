import uuid
from datetime import datetime
import pytz
from django.contrib.auth.models import User
from django.utils.deprecation import MiddlewareMixin
from user.models import RequestTracking
import json

class RequestIDMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request_id = uuid.uuid4().hex
        request.request_id = request_id
        
        try:
            request_body = request.body.decode('utf-8')
        except UnicodeDecodeError:
            request_body = "[Unable to decode request body]"

        request.request_body = request_body

        request_tracking = RequestTracking(
            request_id=request_id,
            start_time=datetime.now(pytz.utc),
            payload=request_body,
            api=request.path,
            request_method=request.method,
        )
        request_tracking.save()

        request.request_tracking = request_tracking

        return None

    def process_response(self, request, response):
        request_tracking = getattr(request, 'request_tracking', None)
        if request_tracking:
            request_tracking.end_time = datetime.now(pytz.utc)
            
            # Extract status code and error message from response body
            status_code = response.status_code
            error_message = None

            try:
                if response.content:
                    body_data = json.loads(response.content.decode('utf-8'))
                    if 'error' in body_data and body_data['error']:  # Check if 'error' is not empty
                        status_code = body_data.get('status', status_code)
                        error_message = body_data['error']
                    else:
                        status_code = body_data.get('status', status_code)
            except Exception as e:
                print(f"Error extracting status code from response body: {e}")

            request_tracking.status = status_code
            if error_message:
                request_tracking.error_message = error_message

            
            # Set the created_by field
            user = request.user if request.user.is_authenticated else None
            request_tracking.created_by = user.username if user else None
            
            request_tracking.save()

        return response