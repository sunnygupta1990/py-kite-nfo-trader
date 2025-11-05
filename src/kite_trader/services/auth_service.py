#!/usr/bin/env python3
"""
Authentication Service for Kite Connect API

This module handles all authentication-related functionality including
automatic login, token management, and session handling.
"""

import webbrowser
import time
import threading
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Tuple

from ..core.config import KiteConfig


class RedirectHandler(BaseHTTPRequestHandler):
    """HTTP handler to capture the redirect URL with request token"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        if 'request_token' in query_params:
            request_token = query_params['request_token'][0]
            action = query_params.get('action', [''])[0]
            status = query_params.get('status', [''])[0]
            
            print(f"\n✅ Redirect captured!")
            print(f"Request Token: {request_token}")
            
            self.server.request_token = request_token
            self.server.auth_success = True
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            success_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authentication Successful</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    .success { color: green; font-size: 24px; }
                    .info { color: #666; margin-top: 20px; }
                </style>
            </head>
            <body>
                <div class="success">✅ Authentication Successful!</div>
                <div class="info">
                    <p>Your request token has been captured.</p>
                    <p>You can close this window and return to the terminal.</p>
                    <p>Session is being established...</p>
                </div>
            </body>
            </html>
            """
            
            self.wfile.write(success_html.encode())
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>Authentication Error</h1>")
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


class AuthService:
    """Service for handling Kite Connect authentication"""
    
    def __init__(self, config: KiteConfig):
        self.config = config
        self.server = None
    
    def start_redirect_server(self, port: int = 8080) -> bool:
        """Start a local HTTP server to capture the redirect"""
        try:
            self.server = HTTPServer(('localhost', port), RedirectHandler)
            self.server.request_token = None
            self.server.auth_success = False
            
            server_thread = threading.Thread(target=self.server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            print(f"✅ Redirect server started on http://localhost:{port}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start redirect server: {e}")
            return False
    
    def stop_redirect_server(self):
        """Stop the redirect server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
    
    def authenticate_automatically(self, kite) -> Tuple[bool, str]:
        """
        Automatically authenticate with Kite Connect API
        
        Args:
            kite: KiteConnect instance
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        print("="*70)
        print("AUTOMATIC AUTHENTICATION")
        print("="*70)
        
        # Check if already authenticated
        if self.config.is_authenticated():
            try:
                api_key = self.config.get_api_key()
                access_token = self.config.get_access_token()
                
                kite.set_access_token(access_token)
                
                # Test connection
                profile = kite.profile()
                print(f"✅ Already authenticated as: {profile.get('user_name', 'N/A')} ({profile.get('user_id', 'N/A')})")
                return True, f"Already authenticated as {profile.get('user_name', 'N/A')}"
                
            except Exception as e:
                print(f"⚠️  Existing token invalid: {e}")
                print("🔄 Generating new access token...")
        
        # Generate new access token
        if not self.config.is_configured():
            return False, "No credentials configured!"
        
        try:
            # Start redirect server
            if not self.start_redirect_server():
                return False, "Failed to start redirect server"
            
            # Generate login URL
            login_url = kite.login_url()
            print(f"✅ Login URL generated: {login_url}")
            
            # Open browser
            try:
                webbrowser.open(login_url)
                print("✅ Login page opened in browser!")
            except Exception as e:
                print(f"⚠️  Could not open browser: {e}")
                print(f"Please visit: {login_url}")
            
            # Wait for redirect
            print(f"⏳ Waiting for authentication (timeout: 300 seconds)...")
            start_time = time.time()
            
            while time.time() - start_time < 300:
                if self.server and self.server.auth_success:
                    request_token = self.server.request_token
                    break
                time.sleep(1)
            else:
                return False, "Authentication timeout!"
            
            # Generate session
            print("🔄 Generating session...")
            api_secret = self.config.get_api_secret()
            data = kite.generate_session(request_token, api_secret=api_secret)
            
            # Save tokens
            self.config.set_tokens(data["access_token"], data.get("refresh_token", ""))
            
            # Update user info
            if "user_id" in data:
                self.config.config["user_id"] = data["user_id"]
            if "user_name" in data:
                self.config.config["user_name"] = data["user_name"]
            if "broker" in data:
                self.config.config["broker"] = data["broker"]
            
            self.config.save_config()
            
            print("✅ Authentication successful!")
            print(f"User: {data.get('user_name', 'N/A')} ({data.get('user_id', 'N/A')})")
            print(f"Broker: {data.get('broker', 'N/A')}")
            
            return True, f"Authenticated as {data.get('user_name', 'N/A')}"
            
        except Exception as e:
            return False, f"Authentication failed: {e}"
        finally:
            self.stop_redirect_server()
    
    def refresh_session(self, kite) -> Tuple[bool, str]:
        """
        Refresh the current session
        
        Args:
            kite: KiteConnect instance
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        print("="*70)
        print("REFRESHING SESSION")
        print("="*70)
        
        success, message = self.authenticate_automatically(kite)
        if success:
            return True, "Session refreshed successfully!"
        else:
            return False, f"Failed to refresh session: {message}"
