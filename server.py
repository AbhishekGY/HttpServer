import asyncio
import socket
import urllib.parse

# Import the router from our module
from router import router
# Import route handlers (this will register them with the router)
import routes

def parse_http_request(request_data):
    """Parse HTTP request data into components."""
    # Split the request into lines
    lines = request_data.split('\r\n')
    
    # Parse the request line (e.g., "GET /index.html HTTP/1.1")
    if not lines or not lines[0]:
        return None
    
    request_line = lines[0].split(' ')
    if len(request_line) != 3:
        return None
    
    method, path, version = request_line
    
    # Parse headers
    headers = {}
    line_index = 1
    while line_index < len(lines) and lines[line_index]:
        header_line = lines[line_index]
        colon_index = header_line.find(':')
        if colon_index != -1:
            header_name = header_line[:colon_index].strip()
            header_value = header_line[colon_index + 1:].strip()
            headers[header_name] = header_value
        line_index += 1
    
    # Parse body (if any)
    body = ""
    if line_index < len(lines) - 1:
        body = '\r\n'.join(lines[line_index + 1:])
    
    # Parse URL and query parameters
    url_parts = urllib.parse.urlparse(path)
    path = url_parts.path
    query_params = urllib.parse.parse_qs(url_parts.query)
    
    return {
        'method': method,
        'path': path,
        'version': version,
        'headers': headers,
        'body': body,
        'query_params': query_params
    }

def format_http_response(response_data):
    """Format a response dictionary into an HTTP response string."""
    # Extract information from the response data
    status = response_data.get('status', '200 OK')
    headers = response_data.get('headers', {})
    body = response_data.get('body', '')
    
    # Ensure body is string for length calculation and final encoding
    if isinstance(body, bytes):
        body = body.decode('utf-8')
    
    # Add Content-Length header if not present
    if 'Content-Length' not in headers:
        headers['Content-Length'] = len(body.encode('utf-8'))
    
    # Format the response
    response_lines = [f"HTTP/1.1 {status}"]
    
    for name, value in headers.items():
        response_lines.append(f"{name}: {value}")
    
    # Join the headers with the body
    response = '\r\n'.join(response_lines) + '\r\n\r\n' + body
    
    return response.encode('utf-8')

async def handle_client(reader, writer):
    """Handle a client connection asynchronously."""
    addr = writer.get_extra_info('peername')
    print(f"Connection from {addr}")
    
    try:
        # Read data from client
        request_data = await reader.read(4096)
        
        if not request_data:
            writer.close()
            return
            
        # Decode the request data
        request_str = request_data.decode('utf-8')
        
        # Parse the request
        parsed_request = parse_http_request(request_str)
        if not parsed_request:
            # Send 400 Bad Request if parsing failed
            response = "HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\nContent-Length: 11\r\n\r\nBad Request"
            writer.write(response.encode('utf-8'))
            await writer.drain()
            return
        
        # Log the parsed request (excluding body for brevity)
        log_request = {k: v for k, v in parsed_request.items() if k != 'body'}
        print(f"Parsed request: {log_request}")
        
        # Use the router to dispatch the request
        response_data = await router.dispatch(parsed_request)
        
        # Format the response as an HTTP response
        response = format_http_response(response_data)
        
        # Send the response
        writer.write(response)
        await writer.drain()
        
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
        try:
            # Send a 500 error response
            error_response = "HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/plain\r\nContent-Length: 21\r\n\r\nInternal Server Error"
            writer.write(error_response.encode('utf-8'))
            await writer.drain()
        except:
            pass
    finally:
        try:
            writer.close()
        except:
            pass

class CustomStreamReaderProtocol(asyncio.StreamReaderProtocol):
    """Custom StreamReaderProtocol to fix the _closed attribute issue."""
    
    def __init__(self, stream_reader, client_connected_cb, loop):
        super().__init__(stream_reader, client_connected_cb, loop)
        # Initialize _closed as a Future, not a boolean
        if not hasattr(self, '_closed'):
            self._closed = loop.create_future()

async def create_server(host='localhost', port=8080):
    """Create and run the async HTTP server."""
    # Create a socket object
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Set socket option to reuse address
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind the socket to the address and port
    sock.bind((host, port))
    
    # Set the socket to non-blocking mode
    sock.setblocking(False)
    
    # Start listening
    sock.listen(100)
    
    # Get the event loop
    loop = asyncio.get_running_loop()
    
    # Create a server using our custom protocol
    server = await loop.create_server(
        lambda: CustomStreamReaderProtocol(
            asyncio.StreamReader(), handle_client, loop
        ),
        sock=sock
    )
    
    # Get available routes for logging
    available_routes = set(path for _, path in router.routes.keys())
    available_methods = {}
    for method, path in router.routes.keys():
        if path not in available_methods:
            available_methods[path] = []
        available_methods[path].append(method)
    
    print(f"Server started on {host}:{port}")
    print("Available routes:")
    for path, methods in available_methods.items():
        print(f"  {path} [{', '.join(methods)}]")
    
    # Keep the server running
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(create_server())
    except KeyboardInterrupt:
        print("Server shutting down...")