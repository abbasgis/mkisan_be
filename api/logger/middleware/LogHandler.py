"""
Middleware to log all requests and responses.
Uses a logger configured by the name of django.request
to log all requests and responses according to configuration
specified for django.request.
"""
# import json
import logging
import traceback
from threading import local

from django.contrib import messages
from django.shortcuts import render

from django.utils.deprecation import MiddlewareMixin

import socket
import time

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from api.logger.models import ActivityLog, LogType

_log_data = local()


class LogHandlerMiddleware(MiddlewareMixin):
    """Request Logging Middleware."""

    def __init__(self, *args, **kwargs):
        """Constructor method."""
        super().__init__(*args, **kwargs)

    def process_request(self, request):
        """Set Request Start Time to measure time taken to service request."""
        if request.method in ['POST', 'PUT', 'PATCH']:
            request.req_body = request.body
        request.start_time = time.time()

    def extract_log_info(self, request, response=None, exception=None):
        """Extract appropriate log info from requests/responses/exceptions."""
        _log_data.value = {
            'remote_address': request.META['REMOTE_ADDR'][:100],
            'server_hostname': socket.gethostname()[:100],
            'request_method': request.method[:10],
            'request_path': request.get_full_path()[:100],
            'run_time': (time.time() - request.start_time) / 1000,
        }

        if request.method in ['PUT', 'POST', 'PATCH']:
            _log_data.value['request_body'] = str(request.req_body)[:200]
        return _log_data.value

    def process_response(self, request, response):
        """Log data using logger."""
        log_data = self.extract_log_info(request=request, response=response)
        if not self.request_path_exceptions(log_data):
            ActivityLog().log_message(log_data, LogType.Info)
        # if log_data['request_path'].find('api/') !=-1:
        #     msg = {"msg": "Request couldn't entertain. Please check with administrator"}
        #     response = Response(msg, status=status.HTTP_400_BAD_REQUEST)
        return response

    def process_exception(self, request, exception):
        """Log Exceptions."""
        log_data = self.extract_log_info(request=request, exception=exception)
        if not self.request_path_exceptions(log_data):
            logger = logging.getLogger()
            logger.error(traceback.format_exc())
            # print(traceback.format_exc())
            # traceback.print_stack()

            log_data['message'] = str(exception)[:200]
            log_data['stack_trace'] = traceback.format_exc()
            ActivityLog().log_message(log_data, LogType.Err)
        return None

    def request_path_exceptions(self, log_data):
        skip_path = ['/admin/logger', '/admin/jsi18n/', '/favicon.ico', '/api/doc/']
        for path in skip_path:
            if log_data['request_path'].find(path) != -1:
                return True
        return False


def api_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    # response = exception_handler(exc, context)
    request = context['request']
    run_time = (time.time() - request.start_time) / 1000 if hasattr(request, 'start_time') else 0
    log_data = {
        'remote_address': request.META['REMOTE_ADDR'][:100],
        'server_hostname': socket.gethostname()[:100],
        'request_method': request.method[:10],
        'request_path': request.get_full_path()[:100],
        'run_time': run_time,
        'request_params': context['kwargs'],
        'message': str(exc)[:200],
        'stack_trace': traceback.format_exc()
    }
    logger = logging.getLogger()
    logger.error(traceback.format_exc())

    ActivityLog().log_message(log_data, LogType.Err)
    msg = {"msg": str(exc)}
    response = Response(msg, status=status.HTTP_400_BAD_REQUEST)
    # Now add the HTTP status code to the response.
    if response is not None:
        response.data['status_code'] = response.status_code
    return response
