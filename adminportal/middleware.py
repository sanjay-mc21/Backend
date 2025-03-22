import time
import logging
import json
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware to log details of all HTTP requests and responses."""
    
    def process_request(self, request):
        """Log details of the request."""
        request.start_time = time.time()
        
        # Log request details
        logger.info(f"Request Method: {request.method}")
        logger.info(f"Request Path: {request.path}")
        logger.info(f"Request Content Type: {request.content_type}")
        logger.info(f"Request Headers: {dict(request.headers)}")
        
        if request.body:
            try:
                # Try to decode body as JSON
                body = json.loads(request.body)
                logger.info(f"Request Body (JSON): {body}")
            except json.JSONDecodeError:
                # If not JSON, log as is
                logger.info(f"Request Body (raw): {request.body}")
        
        return None
    
    def process_response(self, request, response):
        """Log details of the response."""
        # Calculate request duration
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            logger.info(f"Request duration: {duration:.2f}s")
        
        # Log response details
        logger.info(f"Response Status: {response.status_code}")
        logger.info(f"Response Content Type: {response.get('Content-Type', 'unknown')}")
        
        if hasattr(response, 'content'):
            try:
                # Try to decode content as JSON
                content = json.loads(response.content)
                logger.info(f"Response Content (JSON): {content}")
            except (json.JSONDecodeError, UnicodeDecodeError):
                # If not JSON, log a summary
                logger.info(f"Response Content (summary): {str(response.content)[:200]}...")
        
        # Handle CORS preflight requests (OPTIONS)
        if request.method == 'OPTIONS' and request.path == '/api/users/':
            # Log that we're handling a CORS preflight request
            logger.info("Handling CORS preflight request for /api/users/")
            
            # Ensure CORS headers are present
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
        
        return response 