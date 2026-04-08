import socket
try:
    print(f"Resolving google.com: {socket.gethostbyname('google.com')}")
    print(f"Resolving www.google.com: {socket.gethostbyname('www.google.com')}")
except Exception as e:
    print(f"Error resolving: {e}")
