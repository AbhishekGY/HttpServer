import json
from router import router
from middleware import logger_middleware, json_body_parser, request_timing, cors_middleware

# Register global middleware
router.use(logger_middleware)
router.use(request_timing)
router.use(json_body_parser)
router.use(cors_middleware)

# Define a custom middleware just for a specific route
async def auth_middleware(request, response=None):
    """Simple auth middleware that checks for an API key."""
    api_key = request['headers'].get('Authorization')
    if not api_key or api_key != 'Bearer secret-token':
        return {
            'status': '401 Unauthorized',
            'headers': {'Content-Type': 'application/json'},
            'body': '{"error": "Unauthorized. Valid API key required."}'
        }
    return None

@router.get('/')
async def home(request):
    return {
        'status': '200 OK',
        'headers': {'Content-Type': 'text/html'},
        'body': '<html><body><h1>Welcome to the Home Page</h1></body></html>'
    }

@router.get('/about')
async def about(request):
    return {
        'status': '200 OK',
        'headers': {'Content-Type': 'text/html'},
        'body': '<html><body><h1>About Us</h1><p>This is a simple async HTTP server.</p></body></html>'
    }

@router.post('/contact')
async def contact_form(request):
    return {
        'status': '200 OK',
        'headers': {'Content-Type': 'text/html'},
        'body': '<html><body><h1>Thank You!</h1><p>Your message has been received.</p></body></html>'
    }

# Add route-specific middleware to protect this endpoint
@router.get('/api/users', middleware=[auth_middleware])
async def get_users(request):
    return {
        'status': '200 OK',
        'headers': {'Content-Type': 'application/json'},
        'body': '{"users": ["user1", "user2", "user3"]}'
    }

@router.post('/api/users', middleware=[auth_middleware])
async def create_user(request):
    # Since we have json_body_parser middleware, we can access request['json']
    if 'json' in request:
        user_data = request['json']
        # Process user data here
        return {
            'status': '201 Created',
            'headers': {'Content-Type': 'application/json'},
            'body': '{"message": "User created successfully", "user": ' + json.dumps(user_data) + '}'
        }
    else:
        return {
            'status': '400 Bad Request',
            'headers': {'Content-Type': 'application/json'},
            'body': '{"error": "No JSON data provided"}'
        }

@router.not_found
async def not_found(request):
    return {
        'status': '404 Not Found',
        'headers': {'Content-Type': 'text/html'},
        'body': '<html><body><h1>404 Not Found</h1><p>The requested resource was not found on this server.</p></body></html>'
    }