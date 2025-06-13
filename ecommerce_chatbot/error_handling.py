from django.http import JsonResponse
from django.core.exceptions import PermissionDenied, ValidationError
from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
import logging
import traceback
from functools import wraps

logger = logging.getLogger(__name__)

class CustomAPIException(APIException):
    """Custom API exception with additional context."""
    def __init__(self, detail, code=None, context=None):
        super().__init__(detail, code)
        self.context = context or {}

def custom_exception_handler(exc, context):
    """Custom exception handler for DRF."""
    response = exception_handler(exc, context)
    
    if response is not None:
        data = response.data
        if isinstance(data, dict):
            data['status_code'] = response.status_code
            if hasattr(exc, 'context'):
                data['context'] = exc.context
        response.data = data
    
    return response

def handle_api_error(func):
    """Decorator for handling API errors."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CustomAPIException as e:
            logger.error(f"API Error: {str(e)}", extra={'context': e.context})
            return JsonResponse({
                'error': str(e),
                'status_code': e.status_code,
                'context': e.context
            }, status=e.status_code)
        except Exception as e:
            logger.error(f"Unexpected Error: {str(e)}\n{traceback.format_exc()}")
            return JsonResponse({
                'error': 'An unexpected error occurred',
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return wrapper

def handle_view_error(func):
    """Decorator for handling view errors."""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except PermissionDenied:
            logger.warning(f"Permission Denied: {request.user}")
            return JsonResponse({
                'error': 'You do not have permission to perform this action',
                'status_code': status.HTTP_403_FORBIDDEN
            }, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            logger.warning(f"Validation Error: {str(e)}")
            return JsonResponse({
                'error': str(e),
                'status_code': status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected Error: {str(e)}\n{traceback.format_exc()}")
            return JsonResponse({
                'error': 'An unexpected error occurred',
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return wrapper

class ErrorRecovery:
    """Class for handling error recovery strategies."""
    
    @staticmethod
    def retry_operation(operation, max_retries=3, delay=1):
        """Retry an operation with exponential backoff."""
        import time
        from functools import wraps
        
        @wraps(operation)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return operation(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        raise
                    time.sleep(delay * (2 ** (retries - 1)))
            return None
        return wrapper
    
    @staticmethod
    def fallback_response(default_response):
        """Provide a fallback response if the main operation fails."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Operation failed, using fallback: {str(e)}")
                    return default_response
            return wrapper
        return decorator
    
    @staticmethod
    def circuit_breaker(max_failures=3, reset_timeout=60):
        """Circuit breaker pattern implementation."""
        import time
        from functools import wraps
        
        def decorator(func):
            failures = 0
            last_failure_time = 0
            circuit_open = False
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                nonlocal failures, last_failure_time, circuit_open
                
                # Check if circuit is open
                if circuit_open:
                    if time.time() - last_failure_time > reset_timeout:
                        circuit_open = False
                        failures = 0
                    else:
                        raise CustomAPIException(
                            "Service temporarily unavailable",
                            status.HTTP_503_SERVICE_UNAVAILABLE
                        )
                
                try:
                    result = func(*args, **kwargs)
                    failures = 0
                    return result
                except Exception as e:
                    failures += 1
                    last_failure_time = time.time()
                    
                    if failures >= max_failures:
                        circuit_open = True
                    
                    raise
            return wrapper
        return decorator

def log_error(error, context=None):
    """Log an error with context."""
    error_context = {
        'error': str(error),
        'traceback': traceback.format_exc(),
        'context': context or {}
    }
    logger.error("Error occurred", extra=error_context)
    return error_context

def handle_database_error(func):
    """Decorator for handling database errors."""
    from django.db import DatabaseError
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DatabaseError as e:
            logger.error(f"Database Error: {str(e)}")
            return JsonResponse({
                'error': 'Database operation failed',
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return wrapper

def handle_validation_error(func):
    """Decorator for handling validation errors."""
    from django.core.exceptions import ValidationError
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation Error: {str(e)}")
            return JsonResponse({
                'error': str(e),
                'status_code': status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
    return wrapper 