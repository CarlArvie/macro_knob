import http.server
import socketserver
import json
import os
import sys
import webbrowser
import threading
import time

PORT = 8080
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "config.json")
UI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui")

class ConfigRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=UI_DIR, **kwargs)

    def do_GET(self):
        if self.path == '/api/config':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config_data = f.read()
                self.wfile.write(config_data.encode('utf-8'))
            except Exception as e:
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/save':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                # Validate JSON
                new_config = json.loads(post_data.decode('utf-8'))
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
                
                # Write formatted JSON
                with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                    json.dump(new_config, f, indent=4)
                    
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
                
                # Notify Daemon to reload config automatically
                import ctypes
                HWND = ctypes.windll.user32.FindWindowW("KnobLaunchDaemon", "KnobLaunchDaemonWindow")
                if HWND:
                    WM_COMMAND = 0x0111
                    ctypes.windll.user32.PostMessageW(HWND, WM_COMMAND, 40003, 0)

                # Shut down server after successful save
                print("Config saved. Shutting down server...")
                threading.Thread(target=self.server.shutdown).start()
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

def find_available_port(start_port):
    import socket
    port = start_port
    while port < start_port + 100:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                port += 1
    return start_port

def run_server():
    port = find_available_port(PORT)
    
    class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        daemon_threads = True
        allow_reuse_address = True

    with ThreadedTCPServer(("127.0.0.1", port), ConfigRequestHandler) as httpd:
        url = f"http://127.0.0.1:{port}"
        print(f"Serving UI at {url}")
        
        # Open default browser
        webbrowser.open(url)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    run_server()
