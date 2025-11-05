#!/usr/bin/env python3
"""
Main Application Class

This module contains the main application logic that orchestrates
all the services and handles the main application flow.
"""

import sys
import os
from typing import Optional

# Add the pykiteconnect directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'pykiteconnect'))

from kiteconnect import KiteConnect

from .config import KiteConfig
from .app_config import AppConfig
from ..services.auth_service import AuthService
from ..services.nfo_service import NFOService
from ..services.market_data_service import MarketDataService
from ..ui.menu_service import MenuService


class KiteTraderApp:
    """Main application class for Kite Trader"""
    
    def __init__(self):
        """Initialize the application"""
        self.config = KiteConfig()
        self.app_config = AppConfig()
        self.kite: Optional[KiteConnect] = None
        self.is_authenticated = False
        
        # Initialize services
        self.auth_service = AuthService(self.config)
        self.nfo_service = NFOService(self.config)
        self.market_data_service = MarketDataService()
        self.menu_service = MenuService(
            self.config, 
            self.auth_service, 
            self.nfo_service, 
            self.market_data_service
        )
    
    def initialize_kite_connection(self) -> bool:
        """
        Initialize Kite Connect connection
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            api_key = self.config.get_api_key()
            if not api_key:
                print("❌ No API key configured!")
                return False
            
            # Timeout configurable via app_config
            self.kite = KiteConnect(api_key=api_key, disable_ssl=True, timeout=self.app_config.get_timeout())
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize Kite connection: {e}")
            return False
    
    def authenticate(self) -> bool:
        """
        Authenticate with Kite Connect
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.initialize_kite_connection():
            return False
        
        success, message = self.auth_service.authenticate_automatically(self.kite)
        
        if success:
            print(f"\n✅ {message}")
            self.is_authenticated = True
            return True
        else:
            print(f"❌ {message}")
            return False
    
    def run(self) -> bool:
        """
        Run the main application
        
        Returns:
            bool: True if successful, False otherwise
        """
        print("Kite Connect NFO Trader")
        print("Complete solution for NFO trading with Kite Connect API")
        print("="*70)
        
        # Authenticate
        if not self.authenticate():
            print("❌ Authentication failed!")
            return False
        
        print(f"\n✅ Session established successfully!")
        print(f"📅 Current month: {self.nfo_service.current_month}")
        
        # Main loop
        while True:
            try:
                self.menu_service.display_menu()
                choice = self.menu_service.get_user_choice()
                
                if choice == 1:
                    self.menu_service.handle_fetch_contracts(self.kite)
                elif choice == 2:
                    self.menu_service.handle_account_info(self.kite)
                elif choice == 3:
                    self.menu_service.handle_orders(self.kite)
                elif choice == 4:
                    self.menu_service.handle_positions(self.kite)
                elif choice == 5:
                    self.menu_service.handle_holdings(self.kite)
                elif choice == 6:
                    self.menu_service.handle_market_quote(self.kite)
                elif choice == 7:
                    self.menu_service.handle_search_instruments(self.kite)
                elif choice == 8:
                    self.menu_service.handle_options_up_200_percent(self.kite)
                elif choice == 9:
                    self.menu_service.handle_refresh_session(self.kite)
                elif choice == 10:
                    print("\n👋 Goodbye! Session ended.")
                    break
                elif choice == 12:
                    self.menu_service.handle_start_scheduler()
                elif choice == 13:
                    self.menu_service.handle_cleanup()
                else:
                    print("❌ Invalid choice! Please try again.")
                
                input("\nPress Enter to continue...")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Session ended by user.")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                input("Press Enter to continue...")
        
        return True
