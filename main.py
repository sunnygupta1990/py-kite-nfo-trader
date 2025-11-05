#!/usr/bin/env python3
"""
Kite Connect NFO Trader - Main Entry Point

This is the main entry point for the Kite Connect NFO Trader application.
It follows clean architecture principles with separation of concerns.

Usage: python main.py
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from kite_trader.core.app import KiteTraderApp


def main():
    """Main function - entry point of the application"""
    try:
        # Create and optionally run connectivity test
        app = KiteTraderApp()

        if len(sys.argv) > 1 and sys.argv[1] == "--test-conn":
            # Initialize and authenticate
            if not app.authenticate():
                return 1
            ok = app.nfo_service.test_connectivity(app.kite)
            return 0 if ok else 1

        # Default: run the full application
        success = app.run()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n👋 Application terminated by user.")
        return 0
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
