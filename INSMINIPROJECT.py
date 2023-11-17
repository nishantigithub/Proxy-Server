import socket
import threading
import os
import hashlib
import time
from datetime import datetime, timedelta

# Define the proxy server's address and port
PROXY_HOST = '127.0.0.1'
PROXY_PORT = 3000

# Create a directory to store cached web pages
CACHE_DIR = 'cache'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# Cache expiration time (in seconds)
CACHE_EXPIRATION = 3600  # Set to one hour for demonstration purposes

# Cache dictionary to keep track of cached pages and their expiration times
cache = {}

# Create a socket for the proxy server
proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
proxy_socket.bind((PROXY_HOST, PROXY_PORT))
proxy_socket.listen(5)

print(f"Proxy server is listening on {PROXY_HOST}:{PROXY_PORT}")

# Function to check if a cached page is still valid
def is_cache_valid(filename):
    if filename not in cache:
        return False
    
    expiration_time = cache[filename]
    return expiration_time > time.time()

# Function to handle client requests
def handle_client(client_socket):
    # Receive data from the client
    request_data = client_socket.recv(4096)

    # Split the request data into lines
    request_lines = request_data.decode().split('\n')

    # Ensure that there is at least one line in the request
    if len(request_lines) < 1:
        client_socket.close()
        return

    # Extract the first line (HTTP request line)
    first_line = request_lines[0]

    # Split the first line into parts
    parts = first_line.split(' ')

    # Check if the first line has the expected number of parts
    if len(parts) < 3:
        client_socket.close()
        return

    # Extract the requested URL
    url = parts[1]

    # Generate a filename for the cached page (use a hash of the URL)
    filename = os.path.join(CACHE_DIR, hashlib.md5(url.encode()).hexdigest())

    # Check if the requested page is in the cache and still valid
    if is_cache_valid(filename):
        # If it's in the cache and valid, serve it from there
        print(f"Cache hit for {url}")
        with open(filename, 'rb') as cache_file:
            response_data = cache_file.read()
    else:
        # If it's not in the cache or expired, forward the request to the target server
        print(f"Cache miss for {url}")
        target_host = 'www.google.com'
        target_port = 80

        target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target_socket.connect((target_host, target_port))
        target_socket.send(request_data)

        # Receive data from the target server and forward it to the client
        response_data = b''
        while True:
            target_response = target_socket.recv(4096)
            if len(target_response) == 0:
                break
            response_data += target_response
            client_socket.send(target_response)

        # Save the response to the cache and set an expiration time
        with open(filename, 'wb') as cache_file:
            cache_file.write(response_data)
        cache[filename] = time.time() + CACHE_EXPIRATION

    # Close the sockets
    client_socket.close()
    target_socket.close()

# Main loop to accept client connections
while True:
    client_socket, addr = proxy_socket.accept()
    print(f"Accepted connection from {addr[0]}:{addr[1]}")

    # Create a thread to handle the client's request
    client_handler = threading.Thread(target=handle_client, args=(client_socket,))
    client_handler.start()
