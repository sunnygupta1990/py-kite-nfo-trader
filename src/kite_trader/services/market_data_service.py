#!/usr/bin/env python3
"""
Market Data Service

This module handles fetching live market data including LTP, OHLC, volume,
and change percentages for NFO contracts.
"""

from typing import List, Dict, Optional


class MarketDataService:
    """Service for handling market data operations"""
    
    def __init__(self):
        pass
    
    def fetch_ltp_quotes(self, kite, instrument_tokens: List[str]) -> Dict:
        """
        Fetch LTP quotes for instruments using the dedicated LTP endpoint
        
        Args:
            kite: KiteConnect instance
            instrument_tokens: List of instrument tokens
            
        Returns:
            Dict: LTP quotes data
        """
        try:
#            print(f"🔄 Fetching LTP quotes for {len(instrument_tokens)} instruments...")
            
            # Use LTP endpoint for better performance (limit: 1000 instruments)
            batch_size = 1000
            all_ltp_quotes = {}
            
            for i in range(0, len(instrument_tokens), batch_size):
                batch = instrument_tokens[i:i + batch_size]
                try:
                    # Use the dedicated LTP endpoint as per documentation
                    ltp_response = kite.ltp(batch)
                    
                    # Handle the response structure
                    if isinstance(ltp_response, dict) and 'data' in ltp_response:
                        ltp_quotes = ltp_response.get('data', {})
                    elif isinstance(ltp_response, dict):
                        ltp_quotes = ltp_response
                    else:
                        ltp_quotes = {}
                    
                    all_ltp_quotes.update(ltp_quotes)
 #                   print(f"   ✅ Fetched LTP for batch {i//batch_size + 1}/{(len(instrument_tokens)-1)//batch_size + 1} ({len(ltp_quotes)} quotes)")
                    
                except Exception as e:
                    print(f"   ❌ Error fetching LTP batch {i//batch_size + 1}: {e}")
                    continue
            
            print(f"✅ Total LTP quotes retrieved: {len(all_ltp_quotes)}")
            return all_ltp_quotes
            
        except Exception as e:
            print(f"❌ Failed to fetch LTP quotes: {e}")
            return {}
    
    def fetch_full_quotes(self, kite, instrument_tokens: List[str]) -> Dict:
        """
        Fetch full market quotes for detailed data (OHLC, volume, etc.)
        
        Args:
            kite: KiteConnect instance
            instrument_tokens: List of instrument tokens
            
        Returns:
            Dict: Full quotes data
        """
        try:
 #           print(f"🔄 Fetching full market quotes...")
            batch_size = 500  # Limit for full quotes
            all_full_quotes = {}
            
            for i in range(0, len(instrument_tokens), batch_size):
                batch = instrument_tokens[i:i + batch_size]
                try:
                    quotes_response = kite.quote(batch)
                    
                    # Handle response structure
                    if isinstance(quotes_response, dict) and 'data' in quotes_response:
                        quotes = quotes_response.get('data', {})
                    elif isinstance(quotes_response, dict):
                        quotes = quotes_response
                    else:
                        quotes = {}
                    
                    all_full_quotes.update(quotes)
                    print(f"   ✅ Fetched full quotes for batch {i//batch_size + 1}/{(len(instrument_tokens)-1)//batch_size + 1} ({len(quotes)} quotes)")
                    
                except Exception as e:
                    print(f"   ❌ Error fetching full quotes batch {i//batch_size + 1}: {e}")
                    continue
            
            print(f"✅ Total full quotes retrieved: {len(all_full_quotes)}")
            return all_full_quotes
            
        except Exception as e:
            print(f"❌ Failed to fetch full quotes: {e}")
            return {}
    
    def update_contracts_with_market_data(self, contracts: List[Dict], ltp_quotes: Dict, full_quotes: Dict) -> int:
        """
        Update contracts with combined market data
        
        Args:
            contracts: List of contract dictionaries
            ltp_quotes: LTP quotes data
            full_quotes: Full quotes data
            
        Returns:
            int: Number of contracts updated
        """
        updated_count = 0
        
        for contract in contracts:
            symbol = contract.get('tradingsymbol', '')
            quote_key = f"NFO:{symbol}"
            
            # Get LTP from LTP quotes
            ltp = 0
            if quote_key in ltp_quotes:
                ltp = ltp_quotes[quote_key].get('last_price', 0)
            
            # Get detailed data from full quotes
            if quote_key in full_quotes:
                quote_data = full_quotes[quote_key]
                # Use LTP from dedicated LTP endpoint if available, otherwise from full quote
                if ltp > 0:
                    contract['last_price'] = ltp
                else:
                    contract['last_price'] = quote_data.get('last_price', 0)
                
                ohlc = quote_data.get('ohlc', {})
                contract['close_price'] = ohlc.get('close', 0)
                contract['open_price'] = ohlc.get('open', 0)
                contract['high_price'] = ohlc.get('high', 0)
                contract['low_price'] = ohlc.get('low', 0)
                contract['volume'] = quote_data.get('volume', 0)
                
                # Calculate change percentage
                close_price = contract['close_price']
                current_ltp = contract['last_price']
                if close_price > 0 and current_ltp > 0:
                    contract['change_percent'] = round(((current_ltp - close_price) / close_price) * 100, 2)
                else:
                    contract['change_percent'] = 0
                
                updated_count += 1
            elif quote_key in ltp_quotes:
                # Only LTP available
                contract['last_price'] = ltp
                contract['close_price'] = 0
                contract['open_price'] = 0
                contract['high_price'] = 0
                contract['low_price'] = 0
                contract['volume'] = 0
                contract['change_percent'] = 0
                updated_count += 1
            else:
                # No data available
                contract['last_price'] = 0
                contract['close_price'] = 0
                contract['open_price'] = 0
                contract['high_price'] = 0
                contract['low_price'] = 0
                contract['volume'] = 0
                contract['change_percent'] = 0
                print(f"   ⚠️  No data for {symbol}")
        
        return updated_count
    
    def fetch_comprehensive_market_data(self, kite, nfo_service) -> bool:
        """
        Fetch comprehensive market data using both quote and LTP endpoints
        
        Args:
            kite: KiteConnect instance
            nfo_service: NFOService instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"\n🔄 Fetching comprehensive market data for contracts...")
        
        all_contracts = nfo_service.current_month_futures + nfo_service.current_month_options
        if not all_contracts:
            print("❌ No contracts to fetch market data for!")
            return False
        
        try:
            # Prepare instrument list for quote request
            instrument_tokens = []
            for contract in all_contracts:
                symbol = contract.get('tradingsymbol', '')
                if symbol:
                    instrument_tokens.append(f"NFO:{symbol}")
            
            if not instrument_tokens:
                print("❌ No valid instrument tokens found!")
                return False
            
#            print(f"📊 Total instruments to fetch: {len(instrument_tokens)}")
            
            # Step 1: Fetch LTP quotes first (faster, higher limit)
#            print("\n🔄 Step 1: Fetching LTP quotes...")
            ltp_quotes = self.fetch_ltp_quotes(kite, instrument_tokens)
            
            # Step 2: Fetch full quotes for detailed data (OHLC, volume, etc.)
#            print("\n🔄 Step 2: Fetching full market quotes...")
            full_quotes = self.fetch_full_quotes(kite, instrument_tokens)
            
            # Step 3: Update contracts with combined data
            futures_updated = self.update_contracts_with_market_data(nfo_service.current_month_futures, ltp_quotes, full_quotes)
            options_updated = self.update_contracts_with_market_data(nfo_service.current_month_options, ltp_quotes, full_quotes)
            
            print(f"\n✅ Comprehensive market data updated:")
            print(f"   📊 LTP quotes: {len(ltp_quotes)}")
            print(f"   📊 Full quotes: {len(full_quotes)}")
            print(f"   📈 Futures updated: {futures_updated}")
            print(f"   📈 Options updated: {options_updated}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to fetch comprehensive market data: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def find_options_up_percentage(self, kite, nfo_service, percentage: float = 200.0) -> List[Dict]:
        """
        Find options that are up by specified percentage or more
        
        Args:
            kite: KiteConnect instance
            nfo_service: NFOService instance
            percentage: Minimum percentage gain to filter
            
        Returns:
            List[Dict]: List of options meeting the criteria
        """
        print(f"\n🔄 Finding options up {percentage}% or more...")
        
        if not nfo_service.current_month_options:
            print("❌ No options data available!")
            return []
        
        try:
            # Get current quotes for all options
            print("🔄 Fetching current quotes for options...")
            
            # Prepare instrument list for quote request
            option_symbols = []
            for option in nfo_service.current_month_options:
                symbol = option.get('tradingsymbol', '')
                if symbol:
                    option_symbols.append(f"NFO:{symbol}")
            
            if not option_symbols:
                print("❌ No valid option symbols found!")
                return []
            
            # Fetch quotes in batches (Kite API has limits)
            batch_size = 100
            all_quotes = {}
            
            for i in range(0, len(option_symbols), batch_size):
                batch = option_symbols[i:i + batch_size]
                try:
                    quotes = kite.quote(batch)
                    all_quotes.update(quotes)
#                    print(f"   Fetched quotes for batch {i//batch_size + 1}/{(len(option_symbols)-1)//batch_size + 1}")
                except Exception as e:
                    print(f"   ⚠️  Error fetching batch {i//batch_size + 1}: {e}")
                    continue
            
#            print(f"✅ Fetched quotes for {len(all_quotes)} options")
            
            # Analyze options for percentage gains
            options_up_percentage = []
            
            for option in nfo_service.current_month_options:
                symbol = option.get('tradingsymbol', '')
                quote_key = f"NFO:{symbol}"
                
                if quote_key in all_quotes:
                    quote_data = all_quotes[quote_key]
                    current_price = quote_data.get('last_price', 0)
                    ohlc = quote_data.get('ohlc', {})
                    open_price = ohlc.get('open', 0)
                    
                    if current_price > 0 and open_price > 0:
                        # Calculate percentage change
                        percentage_change = ((current_price - open_price) / open_price) * 100
                        
                        if percentage_change >= percentage:
                            options_up_percentage.append({
                                'option': option,
                                'current_price': current_price,
                                'open_price': open_price,
                                'percentage_change': percentage_change,
                                'quote_data': quote_data
                            })
            
            # Sort by percentage change (highest first)
            options_up_percentage.sort(key=lambda x: x['percentage_change'], reverse=True)
            
            return options_up_percentage
            
        except Exception as e:
            print(f"❌ Error analyzing options: {e}")
            import traceback
            traceback.print_exc()
            return []
