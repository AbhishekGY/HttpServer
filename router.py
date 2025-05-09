class Router:
    """A simple HTTP router with decorator support and middleware capabilities."""
    
    def __init__(self):
        self.routes = {}
        self.not_found_handler = None
        self.global_middleware = []  # List to store global middleware
        self.route_middleware = {}   # Dict to store route-specific middleware
    
    def use(self, middleware):
        """Add a global middleware that will run for all routes."""
        self.global_middleware.append(middleware)
        return middleware
    
    def route(self, path, methods=None, middleware=None):
        """Decorator to register a route handler with specified HTTP methods and middleware."""
        if methods is None:
            methods = ['GET']
        if middleware is None:
            middleware = []
        
        def decorator(handler):
            for method in methods:
                key = (method.upper(), path)
                self.routes[key] = handler
                self.route_middleware[key] = middleware
            return handler
        
        return decorator
    
    # Update convenience decorators to support middleware
    def get(self, path, middleware=None):
        """Decorator to register a GET route handler with optional middleware."""
        return self.route(path, methods=['GET'], middleware=middleware)
    
    def post(self, path, middleware=None):
        """Decorator to register a POST route handler with optional middleware."""
        return self.route(path, methods=['POST'], middleware=middleware)
    
    def put(self, path, middleware=None):
        """Decorator to register a PUT route handler with optional middleware."""
        return self.route(path, methods=['PUT'], middleware=middleware)
    
    def delete(self, path, middleware=None):
        """Decorator to register a DELETE route handler with optional middleware."""
        return self.route(path, methods=['DELETE'], middleware=middleware)
    
    def not_found(self, handler):
        """Decorator to register a not found handler."""
        self.not_found_handler = handler
        return handler
    
    async def apply_middleware(self, middleware_list, request, response=None):
        """Apply a list of middleware to the request/response."""
        current_response = response
        
        for middleware in middleware_list:
            # If we already have a response (early return), stop processing
            if current_response:
                break
                
            # Apply the middleware
            result = await middleware(request, current_response)
            
            # If middleware returns a response, use it
            if result:
                current_response = result
        
        return current_response
    
    async def dispatch(self, request):
        """Dispatch a request to the appropriate handler with middleware support."""
        method = request['method'].upper()
        path = request['path']
        key = (method, path)
        
        # Special handling for OPTIONS requests for CORS
        if method == 'OPTIONS':
            response = {
                'status': '204 No Content',
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
                },
                'body': ''
            }
            return response
        
        # Apply global middleware first (pre-processing)
        response = await self.apply_middleware(self.global_middleware, request)
        if response:
            return response
        
        # Try to find an exact match
        handler = self.routes.get(key)
        
        if handler:
            # Apply route-specific middleware if no response yet (pre-processing)
            route_middleware = self.route_middleware.get(key, [])
            response = await self.apply_middleware(route_middleware, request)
            if response:
                return response
                
            # If no middleware returned a response, call the actual handler
            response = await handler(request)
        elif self.not_found_handler:
            response = await self.not_found_handler(request)
        else:
            # Default not found response
            response = {
                'status': '404 Not Found',
                'headers': {'Content-Type': 'text/html'},
                'body': '<html><body><h1>404 Not Found</h1></body></html>'
            }
        
        # Apply post-processing middleware to the response
        # This is for middleware that needs to modify the response
        response = await self.apply_post_middleware(request, response)
        return response

    async def apply_post_middleware(self, request, response):
        """Apply middleware that processes the response after the handler."""
        # For now, we'll just apply the CORS middleware
        for middleware in self.global_middleware:
            # Call the middleware with both request and response
            result = await middleware(request, response)
            if result:
                response = result
        return response

# Create a global router instance
router = Router()