import time
import json

async def logger_middleware(request, response=None):
    """Log information about the incoming request."""
    start_time = time.time()
    print(f"[REQUEST] {request['method']} {request['path']}")
    
    # Let the request continue (don't return a response)
    # We'll log the completion time in a wrapper function
    request['_start_time'] = start_time
    return None

async def request_timing(request, response=None):
    """Calculate and log request processing time."""
    if '_start_time' in request:
        duration = time.time() - request['_start_time']
        print(f"[TIMING] {request['method']} {request['path']} completed in {duration:.4f}s")
    return None

async def json_body_parser(request, response=None):
    """Parse JSON request body if Content-Type is application/json."""
    content_type = request['headers'].get('Content-Type', '')
    
    if 'application/json' in content_type and request['body']:
        try:
            request['json'] = json.loads(request['body'])
            print(f"[JSON] Parsed JSON body: {request['json']}")
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse JSON body: {e}")
            return {
                'status': '400 Bad Request',
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Invalid JSON body'})
            }
    return None

async def cors_middleware(request, response=None):
    """Add CORS headers to all responses."""
    # This will be applied after the route handler in our implementation
    # by modifying the dispatch method, so we expect a response here
    if response:
        headers = response.get('headers', {})
        headers['Access-Control-Allow-Origin'] = '*'
        headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response['headers'] = headers
    return None