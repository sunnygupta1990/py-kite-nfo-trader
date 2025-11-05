#!/usr/bin/env python3
"""
NFO Contract Service

This module handles all NFO-related functionality including
instrument fetching, contract filtering, and market data retrieval.
"""

import os
from datetime import datetime
from typing import List, Dict, Set, Tuple, Optional

from ..core.config import KiteConfig
from ..core.app_config import AppConfig


class NFOService:
    """Service for handling NFO contract operations"""
    
    def __init__(self, config: KiteConfig):
        self.config = config
        self.app_config = AppConfig()
        override = self.app_config.get_month_override()
        self.current_month = override if override else self._get_current_month()
        self.all_instruments = []
        self.current_month_futures = []
        self.current_month_options = []
    
    def _get_current_month(self) -> str:
        """Get current month in correct NFO format (25SEP)"""
        current_year = datetime.now().strftime('%y')
        current_month_name = datetime.now().strftime('%b').upper()
        return f"{current_year}{current_month_name}"

    def _get_next_month_code(self, from_date: Optional[datetime] = None) -> str:
        """Return next month code in NFO format (yyMMM), e.g., 25OCT."""
        d = from_date or datetime.now()
        year = d.year
        month = d.month
        # increment month
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1
        # build code
        next_year_short = str(year % 100).zfill(2)
        next_month_name = datetime(year, month, 1).strftime('%b').upper()
        return f"{next_year_short}{next_month_name}"
    
    def load_nfo_list(self) -> List[str]:
        """Load the complete NFO list from data/Nfo_List.txt"""
        try:
            cfg_path = self.app_config.get_nfo_list_path()
            nfo_list_path = cfg_path if os.path.exists(cfg_path) else os.path.join('data', 'Nfo_List.txt')
            if not os.path.exists(nfo_list_path):
                # Fallback to root directory
                nfo_list_path = 'Nfo_List.txt'
            
            print("🔄 Loading NFO list from Nfo_List.txt...")
            with open(nfo_list_path, 'r', encoding='utf-8') as f:
                nfo_stocks = [line.strip() for line in f.readlines() if line.strip()]
            
            print(f"✅ Loaded {len(nfo_stocks)} stocks from Nfo_List.txt")
            return nfo_stocks
            
        except Exception as e:
            print(f"❌ Failed to load NFO list: {e}")
            return []
    
    def fetch_nfo_instruments(self, kite) -> bool:
        """
        Fetch all NFO instruments and filter by the complete NFO list
        
        Args:
            kite: KiteConnect instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        print("\n" + "="*70)
        print("FETCHING NFO INSTRUMENTS")
        print("="*70)
        
        try:
            print("🔄 Fetching all NFO instruments from API...")
            all_nfo_instruments = kite.instruments("NFO")
            print(f"✅ Retrieved {len(all_nfo_instruments)} total NFO instruments from API")
            
            # Load the complete NFO list
            nfo_stocks_list = self.load_nfo_list()
            if not nfo_stocks_list:
                print("⚠️  No NFO list loaded, using all instruments from API")
                self.all_instruments = all_nfo_instruments
                return True
            
            # Filter instruments to only include those from our NFO list
            print(f"🔄 Filtering instruments to match {len(nfo_stocks_list)} stocks from Nfo_List.txt...")
            filtered_instruments = []
            
            for instrument in all_nfo_instruments:
                instrument_name = instrument.get('name', '').upper()
                if instrument_name in [stock.upper() for stock in nfo_stocks_list]:
                    filtered_instruments.append(instrument)
            
            self.all_instruments = filtered_instruments
            print(f"✅ Filtered to {len(self.all_instruments)} instruments matching NFO list")
            
            # Show summary of found stocks
            found_stocks = set([inst.get('name', '').upper() for inst in self.all_instruments])
            missing_stocks = set([stock.upper() for stock in nfo_stocks_list]) - found_stocks
            
            if missing_stocks:
                print(f"⚠️  {len(missing_stocks)} stocks from NFO list not found in API instruments:")
                for stock in sorted(missing_stocks)[:10]:  # Show first 10
                    print(f"   - {stock}")
                if len(missing_stocks) > 10:
                    print(f"   ... and {len(missing_stocks) - 10} more")
            else:
                print("✅ All stocks from NFO list found in API instruments!")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to fetch NFO instruments: {e}")
            return False
    
    def test_connectivity(self, kite) -> bool:
        """
        Lightweight connectivity test to the NFO instruments endpoint with higher timeout.
        Temporarily bumps client timeout and attempts a minimal fetch.
        """
        try:
            print("\n" + "="*70)
            print("CONNECTIVITY TEST: NFO instruments")
            print("="*70)

            # Temporarily increase timeout if lower than 20s
            original_timeout = getattr(kite, "timeout", 7)
            if original_timeout < 20:
                kite.timeout = 30

            start = datetime.now()
            # Use the official client route which returns CSV under the hood
            instruments = kite.instruments("NFO")
            elapsed = (datetime.now() - start).total_seconds()

            count = len(instruments) if isinstance(instruments, list) else 0
            print(f"✅ Connectivity OK. Retrieved {count} instruments in {elapsed:.2f}s")

            # Basic sanity on content
            if count == 0:
                print("⚠️  Response was empty; API reachable but no data returned.")

            return True

        except Exception as e:
            print(f"❌ Connectivity test failed: {e}")
            return False
        finally:
            # Restore original timeout
            try:
                kite.timeout = original_timeout
            except Exception:
                pass
    def get_current_month_contracts(self) -> bool:
        """
        Filter current month contracts for all stocks in NFO list
        
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"\n🔄 Filtering current month ({self.current_month}) contracts...")
        
        self.current_month_futures = []
        self.current_month_options = []
        
        # Load the NFO list to ensure we track all stocks
        nfo_stocks_list = self.load_nfo_list()
        nfo_stocks_upper = [stock.upper() for stock in nfo_stocks_list]
        
        # Track which stocks have contracts found
        stocks_with_futures = set()
        stocks_with_options = set()
        
        for instrument in self.all_instruments:
            tradingsymbol = instrument.get('tradingsymbol', '')
            instrument_type = instrument.get('instrument_type', '').upper()
            instrument_name = instrument.get('name', '').upper()
            
            # Check if this is a current month contract using the correct format
            if self.current_month in tradingsymbol:
                if instrument_type == 'FUT':
                    self.current_month_futures.append(instrument)
                    stocks_with_futures.add(instrument_name)
                elif instrument_type in ['CE', 'PE']:
                    self.current_month_options.append(instrument)
                    stocks_with_options.add(instrument_name)
        
        print(f"✅ Found {len(self.current_month_futures)} current month futures")
        print(f"✅ Found {len(self.current_month_options)} current month options")

        # Fallback: if no current-month futures, try next-month contracts (configurable)
        if len(self.current_month_futures) == 0 and self.app_config.is_fallback_next_month_enabled():
            next_month = self._get_next_month_code()
            print(f"\n⚠️  No current-month futures found. Trying next-month ({next_month}) contracts...")

            next_month_futures = []
            next_month_options = []
            stocks_with_futures = set()
            stocks_with_options = set()

            for instrument in self.all_instruments:
                tradingsymbol = instrument.get('tradingsymbol', '')
                instrument_type = instrument.get('instrument_type', '').upper()
                instrument_name = instrument.get('name', '').upper()

                if next_month in tradingsymbol:
                    if instrument_type == 'FUT':
                        next_month_futures.append(instrument)
                        stocks_with_futures.add(instrument_name)
                    elif instrument_type in ['CE', 'PE']:
                        next_month_options.append(instrument)
                        stocks_with_options.add(instrument_name)

            if len(next_month_futures) > 0:
                self.current_month = next_month
                self.current_month_futures = next_month_futures
                self.current_month_options = next_month_options
                print(f"✅ Fallback succeeded: Found {len(self.current_month_futures)} next-month futures and {len(self.current_month_options)} options")
            else:
                print("❌ Fallback failed: No next-month futures found either.")
        
        # Report on coverage
        stocks_with_contracts = stocks_with_futures.union(stocks_with_options)
        missing_contracts = set(nfo_stocks_upper) - stocks_with_contracts
        
        print(f"📊 Coverage Report:")
        print(f"   - Stocks with futures: {len(stocks_with_futures)}")
        print(f"   - Stocks with options: {len(stocks_with_options)}")
        print(f"   - Stocks with any contracts: {len(stocks_with_contracts)}")
        
        if missing_contracts:
            print(f"⚠️  {len(missing_contracts)} stocks from NFO list have no current month contracts:")
            # Only show first 20 missing stocks to avoid spam
            for stock in sorted(missing_contracts)[:20]:
                print(f"   - {stock}")
            if len(missing_contracts) > 20:
                print(f"   ... and {len(missing_contracts) - 20} more")
        else:
            print("✅ All stocks from NFO list have current month contracts!")
        
        return True
    
    def get_atm_strike(self, kite, underlying: str) -> float:
        """
        Get ATM strike price for an underlying
        
        Args:
            kite: KiteConnect instance
            underlying: Stock symbol
            
        Returns:
            float: ATM strike price
        """
        # First try to get from NSE spot price
        try:
            quote = kite.quote(f"NSE:{underlying}")
            if f"NSE:{underlying}" in quote:
                ltp = quote[f"NSE:{underlying}"].get('last_price', 0)
                if ltp > 0:
 #                   print(f"     ✅ Got ATM strike from NSE spot: {ltp}")
                    return ltp
                else:
                    print(f"     ⚠️  NSE spot LTP is 0 for {underlying}")
            else:
                print(f"     ⚠️  No NSE spot data found for {underlying}")
        except Exception as e:
            print(f"     ⚠️  Error fetching NSE spot for {underlying}: {e}")
        
        # Try to get from futures (more accurate for ATM)
        for future in self.current_month_futures:
            if future.get('name', '').upper() == underlying.upper():
                ltp = future.get('last_price', 0)
                if ltp > 0:
 #                   print(f"     ✅ Got ATM strike from future: {ltp}")
                    return ltp
                else:
                    print(f"     ⚠️  Future LTP is 0 for {underlying}")
        
        # Last resort: try to get from any available option (not ideal but better than 0)
        for option in self.current_month_options:
            if option.get('name', '').upper() == underlying.upper():
                ltp = option.get('last_price', 0)
                if ltp > 0:
                    print(f"     ⚠️  Using option LTP as fallback ATM strike: {ltp}")
                    return ltp
        
        print(f"     ❌ Could not determine ATM strike for {underlying} from any source")
        return 0
    
    def filter_atm_otm_options(self, kite, max_strikes: int = None) -> bool:
        """
        Filter options to include only ATM and OTM up to specified strikes
        
        Args:
            kite: KiteConnect instance
            max_strikes: Maximum number of strikes on each side of ATM
            
        Returns:
            bool: True if successful, False otherwise
        """
        effective_max = max_strikes if max_strikes is not None else self.app_config.get_options_filter_max_strikes()
        print(f"\n🔄 Filtering options to ATM and OTM up to {effective_max} strikes...")
        
        options_by_underlying = {}
        for option in self.current_month_options:
            underlying = option.get('name', '')
            if underlying not in options_by_underlying:
                options_by_underlying[underlying] = []
            options_by_underlying[underlying].append(option)
        
        filtered_options = []
        processed_count = 0
        skipped_count = 0
        
        print(f"   Processing {len(options_by_underlying)} underlying stocks...")
        
        for underlying, options in options_by_underlying.items():
            processed_count += 1
            if processed_count % 100 == 0:
                print(f"   Progress: {processed_count}/{len(options_by_underlying)} stocks processed...")
            
            atm_strike = self.get_atm_strike(kite, underlying)
            if atm_strike == 0:
                print(f"     ⚠️  Could not determine ATM strike for {underlying}, including all {len(options)} options")
                filtered_options.extend(options)
                skipped_count += 1
                continue
            
            strikes = sorted(set([opt.get('strike', 0) for opt in options]))
            
            atm_index = -1
            for i, strike in enumerate(strikes):
                if abs(strike - atm_strike) < abs(strikes[atm_index] - atm_strike) if atm_index >= 0 else True:
                    atm_index = i
            
            if atm_index == -1:
                print(f"     ⚠️  Could not find ATM strike for {underlying}, including all options")
                filtered_options.extend(options)
                skipped_count += 1
                continue
            
            start_index = max(0, atm_index - effective_max)
            end_index = min(len(strikes), atm_index + effective_max + 1)
            selected_strikes = strikes[start_index:end_index]
            
            # Only print detailed info for first few stocks to avoid spam
            if processed_count <= 5:
                print(f"     {underlying}: ATM={atm_strike}, Selected strikes={selected_strikes}")
            
            for option in options:
                if option.get('strike', 0) in selected_strikes:
                    filtered_options.append(option)
        
        self.current_month_options = filtered_options
        print(f"✅ Filtered to {len(self.current_month_options)} ATM/OTM options from {len(options_by_underlying)} underlying stocks")
        if skipped_count > 0:
            print(f"⚠️  {skipped_count} stocks had issues with ATM calculation and included all their options")
        return True
    
    def get_contract_summary(self) -> Dict:
        """
        Get summary of current contracts
        
        Returns:
            Dict: Summary information
        """
        return {
            'current_month': self.current_month,
            'total_futures': len(self.current_month_futures),
            'total_options': len(self.current_month_options),
            'all_instruments': len(self.all_instruments)
        }
