#!/usr/bin/env python3
"""
Secure Configuration Management for Kite Connect API

This module handles secure storage and management of API credentials.
"""

import os
import json
from typing import Dict, Optional

class KiteConfig:
    """Secure configuration manager for Kite Connect API"""
    
    def __init__(self, config_file: str = "kite_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load configuration from file or create default"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config file: {e}")
                return self._create_default_config()
        else:
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict:
        """Create default configuration structure"""
        return {
            "api_key": "rl88rf5xiafpgl7j",
            "api_secret": "l27kxipokbl1zfoa9dnzenv6toplqekg",
            "access_token": "",
            "refresh_token": "",
            "user_id": "",
            "user_name": "",
            "broker": "",
            "redirect_url": "http://localhost:8080/callback",
            "environment": "production"  # or "paper" for paper trading
        }
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"Configuration saved to {self.config_file}")
        except IOError as e:
            print(f"Error saving configuration: {e}")
    
    def set_credentials(self, api_key: str, api_secret: str, user_id: str = "", user_name: str = "", broker: str = ""):
        """Set API credentials"""
        self.config["api_key"] = api_key
        self.config["api_secret"] = api_secret
        self.config["user_id"] = user_id
        self.config["user_name"] = user_name
        self.config["broker"] = broker
        self.save_config()
    
    def set_tokens(self, access_token: str, refresh_token: str = ""):
        """Set authentication tokens"""
        self.config["access_token"] = access_token
        if refresh_token:
            self.config["refresh_token"] = refresh_token
        self.save_config()
    
    def get_api_key(self) -> str:
        """Get API key"""
        return self.config.get("api_key", "")
    
    def get_api_secret(self) -> str:
        """Get API secret"""
        return self.config.get("api_secret", "")
    
    def get_access_token(self) -> str:
        """Get access token"""
        return self.config.get("access_token", "")
    
    def get_refresh_token(self) -> str:
        """Get refresh token"""
        return self.config.get("refresh_token", "")
    
    def get_user_info(self) -> Dict:
        """Get user information"""
        return {
            "user_id": self.config.get("user_id", ""),
            "user_name": self.config.get("user_name", ""),
            "broker": self.config.get("broker", "")
        }
    
    def is_configured(self) -> bool:
        """Check if basic credentials are configured"""
        return bool(self.config.get("api_key") and self.config.get("api_secret"))
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated (has access token)"""
        return bool(self.config.get("access_token"))
    
    def clear_tokens(self):
        """Clear authentication tokens"""
        self.config["access_token"] = ""
        self.config["refresh_token"] = ""
        self.save_config()
    
    def display_config(self, show_secrets: bool = False):
        """Display current configuration"""
        print("\n" + "="*50)
        print("KITE CONNECT CONFIGURATION")
        print("="*50)
        print(f"API Key: {self.config['api_key'][:8]}..." if self.config['api_key'] else "API Key: Not set")
        if show_secrets:
            print(f"API Secret: {self.config['api_secret']}")
        else:
            print(f"API Secret: {'*' * len(self.config['api_secret'])}" if self.config['api_secret'] else "API Secret: Not set")
        print(f"Access Token: {'Set' if self.config['access_token'] else 'Not set'}")
        print(f"User ID: {self.config['user_id']}")
        print(f"User Name: {self.config['user_name']}")
        print(f"Broker: {self.config['broker']}")
        print(f"Redirect URL: {self.config['redirect_url']}")
        print(f"Environment: {self.config['environment']}")
        print("="*50)

def get_user_credentials():
    """Interactive function to get user credentials"""
    print("\n" + "="*60)
    print("KITE CONNECT API CREDENTIALS SETUP")
    print("="*60)
    print("Please provide your Kite Connect API credentials.")
    print("You can get these from: https://developers.kite.trade/")
    print("="*60)
    
    api_key = input("Enter your API Key: ").strip()
    api_secret = input("Enter your API Secret: ").strip()
    user_id = input("Enter your User ID (optional): ").strip()
    user_name = input("Enter your Name (optional): ").strip()
    broker = input("Enter your Broker (optional): ").strip()
    
    if not api_key or not api_secret:
        print("❌ Error: API Key and API Secret are required!")
        return None, None, None, None, None
    
    return api_key, api_secret, user_id, user_name, broker
