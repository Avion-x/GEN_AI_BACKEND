import uuid
from datetime import datetime
import pytz
from django.contrib.auth.models import User
from django.utils.deprecation import MiddlewareMixin
from user.models import RequestTracking
import json
import threading


# Using thread-local storage to store the request object
_thread_locals = threading.local()

def get_current_request():
    return getattr(_thread_locals, 'request', None)

def set_current_request(request):
    setattr(_thread_locals, 'request', request)

def delete_current_request():
    if hasattr(_thread_locals, 'request'):
        del _thread_locals.request

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
        request_tracking.set_meta({key: value for key, value in request.META.items() if isinstance(value, str)})
        if request.user.is_authenticated:
            request_tracking.created_by = request.user
        request_tracking.save()
        request.request_tracking = request_tracking
        
        _thread_locals.request = request
        return None
        
    def process_response(self, request, response):
        request_tracking = getattr(request, 'request_tracking', None)
        if request_tracking:
            status_code = response.status_code
            error_message = response.content if response.status_code>=400 else None

            try:
                # Extract status code and error message from response body
                body_data = json.loads(response.content.decode('utf-8'))
                status_code = body_data.get('status', status_code)
                error_message = body_data.get('error', error_message)
            except Exception as e:
                print(f"Error extracting status code from response body: {e}")

            request_tracking.status_code = status_code
            request_tracking.error_message = error_message
            # request_tracking.created_by = request.user
            request_tracking.save()

        return response