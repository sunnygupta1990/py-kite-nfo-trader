#!/usr/bin/env python3
"""
Basic tests for Kite Trader application
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from kite_trader.core.config import KiteConfig
from kite_trader.services.auth_service import AuthService
from kite_trader.services.nfo_service import NFOService


def test_config_loading():
    """Test configuration loading"""
    config = KiteConfig()
    assert config is not None
    print("✅ Config loading test passed")


def test_nfo_service_initialization():
    """Test NFO service initialization"""
    config = KiteConfig()
    nfo_service = NFOService(config)
    assert nfo_service is not None
    assert nfo_service.current_month is not None
    print("✅ NFO service initialization test passed")


def test_auth_service_initialization():
    """Test authentication service initialization"""
    config = KiteConfig()
    auth_service = AuthService(config)
    assert auth_service is not None
    print("✅ Auth service initialization test passed")


def test_nfo_list_loading():
    """Test NFO list loading"""
    config = KiteConfig()
    nfo_service = NFOService(config)
    
    # Test loading NFO list
    nfo_list = nfo_service.load_nfo_list()
    assert len(nfo_list) > 0
    print(f"✅ NFO list loading test passed - loaded {len(nfo_list)} stocks")


if __name__ == "__main__":
    print("Running basic tests...")
    test_config_loading()
    test_nfo_service_initialization()
    test_auth_service_initialization()
    test_nfo_list_loading()
    print("\n✅ All basic tests passed!")
