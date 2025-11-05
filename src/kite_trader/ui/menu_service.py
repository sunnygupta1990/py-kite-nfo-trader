#!/usr/bin/env python3
"""
Menu Service

This module handles all user interface and menu operations.
"""

import os
import sys
import subprocess
import json
import glob
import shutil
from datetime import datetime
from typing import List, Dict, Optional

from ..core.config import KiteConfig
from ..services.auth_service import AuthService
from ..services.nfo_service import NFOService
from ..services.market_data_service import MarketDataService
from ..core.app_config import AppConfig


class MenuService:
    """Service for handling user interface and menu operations"""
    
    def __init__(self, config: KiteConfig, auth_service: AuthService, 
                 nfo_service: NFOService, market_data_service: MarketDataService):
        self.config = config
        self.app_config = AppConfig()
        self.auth_service = auth_service
        self.nfo_service = nfo_service
        self.market_data_service = market_data_service
    
    def display_menu(self):
        """Display interactive menu"""
        print("\n" + "="*70)
        print("KITE CONNECT NFO TRADER - MAIN MENU")
        print("="*70)
        print("1. Fetch Current Month NFO Contracts")
        print("2. View Account Information")
        print("3. View Orders")
        print("4. View Positions")
        print("5. View Holdings")
        print("6. Get Market Quote")
        print("7. Search Instruments")
        print("8. List Options Up 200%+")
        print("9. Refresh Session")
        print("10. Exit")
        print("12. Start Scheduler (Option 1 -> Option 8 every N minutes)")
        print("13. Cleanup unnecessary files")
        print("="*70)
    
    def get_user_choice(self) -> int:
        """Get user choice from menu"""
        try:
            choice = input("\nEnter your choice (1-13): ").strip()
            return int(choice)
        except ValueError:
            return 0
    
    def handle_fetch_contracts(self, kite) -> bool:
        """
        Handle fetching NFO contracts
        
        Args:
            kite: KiteConnect instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        print("\n" + "="*70)
        print("FETCHING CURRENT MONTH NFO CONTRACTS")
        print("="*70)
        
        if not self.nfo_service.fetch_nfo_instruments(kite):
            return False
        
        if not self.nfo_service.get_current_month_contracts():
            return False
        
        if not self.market_data_service.fetch_comprehensive_market_data(kite, self.nfo_service):
            return False
        
        if not self.nfo_service.filter_atm_otm_options(kite):
            return False
        
        if not self.save_contracts_to_file():
            return False
        
        summary = self.nfo_service.get_contract_summary()
        print(f"\n✅ Successfully fetched and saved current month NFO contracts!")
        print(f"📁 File: current_month_nfo_contracts.txt")
        print(f"📊 Summary: {summary['total_futures']} futures, {summary['total_options']} options")
        
        return True
    
    def handle_account_info(self, kite):
        """Handle account information display"""
        print("\n" + "="*70)
        print("ACCOUNT INFORMATION")
        print("="*70)
        
        try:
            profile = kite.profile()
            print(f"User Name: {profile.get('user_name', 'N/A')}")
            print(f"User ID: {profile.get('user_id', 'N/A')}")
            print(f"Email: {profile.get('email', 'N/A')}")
            print(f"Broker: {profile.get('broker', 'N/A')}")
            print(f"Products: {', '.join(profile.get('products', []))}")
            
            margins = kite.margins()
            equity = margins.get('equity', {})
            available = equity.get('available', {})
            print(f"\nAvailable Cash: ₹{available.get('cash', 'N/A')}")
            print(f"Available Margin: ₹{available.get('margin', 'N/A')}")
            
        except Exception as e:
            print(f"❌ Error fetching account info: {e}")
    
    def handle_orders(self, kite):
        """Handle orders display"""
        print("\n" + "="*70)
        print("ORDERS")
        print("="*70)
        
        try:
            orders = kite.orders()
            print(f"Total Orders: {len(orders)}")
            
            if orders:
                print(f"\n{'Symbol':<15} {'Type':<4} {'Qty':<6} {'Price':<8} {'Status':<12} {'Time':<20}")
                print("-" * 80)
                for order in orders[:10]:  # Show first 10
                    symbol = order.get('tradingsymbol', 'N/A')
                    txn_type = order.get('transaction_type', 'N/A')
                    qty = order.get('quantity', 0)
                    price = order.get('price', 0)
                    status = order.get('status', 'N/A')
                    time = order.get('order_timestamp', 'N/A')
                    print(f"{symbol:<15} {txn_type:<4} {qty:<6} {price:<8} {status:<12} {time}")
            else:
                print("No orders found")
                
        except Exception as e:
            print(f"❌ Error fetching orders: {e}")
    
    def handle_positions(self, kite):
        """Handle positions display"""
        print("\n" + "="*70)
        print("POSITIONS")
        print("="*70)
        
        try:
            positions = kite.positions()
            day_pos = positions.get('day', [])
            net_pos = positions.get('net', [])
            
            print(f"Day Positions: {len(day_pos)}")
            print(f"Net Positions: {len(net_pos)}")
            
            if day_pos:
                print(f"\nDay Positions:")
                print(f"{'Symbol':<15} {'Qty':<6} {'P&L':<10} {'Value':<10}")
                print("-" * 50)
                for pos in day_pos[:10]:
                    symbol = pos.get('tradingsymbol', 'N/A')
                    qty = pos.get('quantity', 0)
                    pnl = pos.get('pnl', 0)
                    value = pos.get('average_price', 0) * qty
                    print(f"{symbol:<15} {qty:<6} {pnl:<10} {value:<10}")
                    
        except Exception as e:
            print(f"❌ Error fetching positions: {e}")
    
    def handle_holdings(self, kite):
        """Handle holdings display"""
        print("\n" + "="*70)
        print("HOLDINGS")
        print("="*70)
        
        try:
            holdings = kite.holdings()
            print(f"Total Holdings: {len(holdings)}")
            
            if holdings:
                print(f"\n{'Symbol':<15} {'Qty':<6} {'Avg Price':<10} {'LTP':<8} {'P&L':<10}")
                print("-" * 60)
                for holding in holdings[:10]:
                    symbol = holding.get('tradingsymbol', 'N/A')
                    qty = holding.get('quantity', 0)
                    avg_price = holding.get('average_price', 0)
                    ltp = holding.get('last_price', 0)
                    pnl = holding.get('pnl', 0)
                    print(f"{symbol:<15} {qty:<6} {avg_price:<10} {ltp:<8} {pnl:<10}")
            else:
                print("No holdings found")
                
        except Exception as e:
            print(f"❌ Error fetching holdings: {e}")
    
    def handle_market_quote(self, kite):
        """Handle market quote"""
        print("\n" + "="*70)
        print("MARKET QUOTE")
        print("="*70)
        
        symbol = input("Enter symbol (e.g., NSE:RELIANCE): ").strip()
        if not symbol:
            print("❌ No symbol entered!")
            return
        
        try:
            quote_response = kite.quote(symbol)
            
            # Handle response structure according to Kite Connect docs
            if isinstance(quote_response, dict) and 'data' in quote_response:
                quotes = quote_response.get('data', {})
            elif isinstance(quote_response, dict):
                quotes = quote_response
            else:
                quotes = {}
            
            if symbol in quotes:
                data = quotes[symbol]
                print(f"\nQuote for {symbol}:")
                print(f"Last Price (LTP): ₹{data.get('last_price', 'N/A')}")
                print(f"Open: ₹{data.get('ohlc', {}).get('open', 'N/A')}")
                print(f"High: ₹{data.get('ohlc', {}).get('high', 'N/A')}")
                print(f"Low: ₹{data.get('ohlc', {}).get('low', 'N/A')}")
                print(f"Close: ₹{data.get('ohlc', {}).get('close', 'N/A')}")
                print(f"Volume: {data.get('volume', 'N/A')}")
                print(f"Average Price: ₹{data.get('average_price', 'N/A')}")
                
                # Show additional data if available
                if data.get('net_change', 0) != 0:
                    print(f"Net Change: ₹{data.get('net_change', 'N/A')}")
                if data.get('lower_circuit_limit', 0) > 0:
                    print(f"Circuit Limits: ₹{data.get('lower_circuit_limit', 'N/A')} - ₹{data.get('upper_circuit_limit', 'N/A')}")
            else:
                print(f"❌ No data found for {symbol}")
                
        except Exception as e:
            print(f"❌ Error fetching quote: {e}")
    
    def handle_search_instruments(self, kite):
        """Handle instrument search"""
        print("\n" + "="*70)
        print("SEARCH INSTRUMENTS")
        print("="*70)
        
        query = input("Enter search query: ").strip()
        if not query:
            print("❌ No query entered!")
            return
        
        try:
            results = []
            for instrument in self.nfo_service.all_instruments:
                symbol = instrument.get('tradingsymbol', '').upper()
                name = instrument.get('name', '').upper()
                if query.upper() in symbol or query.upper() in name:
                    results.append(instrument)
            
            print(f"\nFound {len(results)} instruments:")
            for instrument in results[:20]:  # Show first 20
                symbol = instrument.get('tradingsymbol', 'N/A')
                name = instrument.get('name', 'N/A')
                inst_type = instrument.get('instrument_type', 'N/A')
                print(f"  {symbol} - {name} ({inst_type})")
                
        except Exception as e:
            print(f"❌ Error searching instruments: {e}")
    
    def handle_options_up_200_percent(self, kite):
        """Handle listing options that are up by 200% or more"""
        print("\n" + "="*70)
        print("OPTIONS UP 200% OR MORE")
        print("="*70)
        
        if not self.nfo_service.current_month_options:
            print("❌ No options data available! Please fetch NFO contracts first (Option 1).")
            return
        
        try:
            threshold = self.app_config.get_options_up_threshold_percent()
            options_up_200 = self.market_data_service.find_options_up_percentage(kite, self.nfo_service, threshold)
            
            if options_up_200:
                print(f"\n🎉 Found {len(options_up_200)} options up by {threshold}% or more!")
                print("\n" + "="*100)
                print(f"{'Symbol':<30} {'Name':<15} {'Type':<4} {'Strike':<8} {'Open':<8} {'Current':<8} {'Change %':<10} {'Volume':<10}")
                print("="*100)
                
                for item in options_up_200:
                    option = item['option']
                    symbol = option.get('tradingsymbol', 'N/A')
                    name = option.get('name', 'N/A')
                    inst_type = option.get('instrument_type', 'N/A')
                    strike = option.get('strike', 0)
                    open_price = item['open_price']
                    current_price = item['current_price']
                    percentage_change = item['percentage_change']
                    volume = item['quote_data'].get('volume', 0)
                    
                    print(f"{symbol:<30} {name:<15} {inst_type:<4} {strike:<8} {open_price:<8} {current_price:<8} {percentage_change:<10.2f} {volume:<10}")
                
                # Save to file
                filename = f"options_up_200_percent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                self.save_options_up_percentage_to_file(options_up_200, filename)
                
            else:
                print(f"\n😔 No options found that are up by {threshold}% or more.")
                print("This could mean:")
                print("- Market conditions are not favorable for such gains")
                print("- Options data needs to be refreshed")
                print("- Try fetching fresh NFO contracts first")
            
        except Exception as e:
            print(f"❌ Error analyzing options: {e}")
            import traceback
            traceback.print_exc()

    def handle_start_scheduler(self):
        """Start the background scheduler and keep the user in a live status view until they exit."""
        print("\n" + "="*70)
        print("START SCHEDULER")
        print("="*70)

        try:
            # Ask for interval override
            user = input("Enter interval in seconds (blank to use config): ").strip()
            args = [sys.executable, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'watch_options_changes.py')]
            if user:
                try:
                    seconds = int(user)
                    if seconds <= 0:
                        raise ValueError
                    args += ["--interval", str(seconds)]
                except ValueError:
                    print("⚠️  Invalid interval, using config value.")

            # Launch watcher in background
            proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"✅ Scheduler started (PID {proc.pid}).")
            print("- Configure interval via output/scheduler_config.json")
            print("- Press Ctrl+C to stop the scheduler and return to the menu")

            # Live status loop: keep user updated
            status_path = os.path.join('output', 'watcher_status.json')
            while True:
                try:
                    print("\n" + "-"*70)
                    print("Scheduler Status (refreshes every 5s)")
                    print("-"*70)
                    if os.path.exists(status_path):
                        with open(status_path, 'r', encoding='utf-8') as f:
                            st = json.load(f)
                        last_run = st.get('last_run', 'N/A')
                        interval = st.get('interval_seconds', 'N/A')
                        added = st.get('added_count', 'N/A')
                        removed = st.get('removed_count', 'N/A')
                        next_eta = st.get('next_run_eta')
                        if isinstance(next_eta, int):
                            import time as _t
                            remaining = max(0, next_eta - int(_t.time()))
                        else:
                            remaining = 'N/A'
                        print(f"Last run: {last_run}")
                        print(f"Interval: {interval}s | Next run in: {remaining}s")
                        print(f"Last change: +{added} / -{removed}")
                    else:
                        print("Waiting for first cycle... (status file not yet created)")

                    # If process exits, break
                    ret = proc.poll()
                    if ret is not None:
                        print(f"\n❌ Scheduler exited with code {ret}.")
                        break

                    import time as _t
                    _t.sleep(5)
                except KeyboardInterrupt:
                    print("\n⏹ Stopping scheduler...")
                    try:
                        proc.terminate()
                        proc.wait(timeout=5)
                    except Exception:
                        try:
                            proc.kill()
                        except Exception:
                            pass
                    print("✅ Scheduler stopped.")
                    break
        except Exception as e:
            print(f"❌ Failed to start scheduler: {e}")

    def handle_cleanup(self):
        """Cleanup unnecessary files: cache, logs, and generated diff/text outputs."""
        print("\n" + "="*70)
        print("CLEANUP FILES")
        print("="*70)

        # Targets
        to_delete_files = []
        # Output diffs and historical option-up text files
        to_delete_files.extend(glob.glob(os.path.join('output', 'options_up_diff_*.txt')))
        to_delete_files.extend(glob.glob(os.path.join('output', 'options_up_200_percent_*.txt')))
        # Keep latest json snapshots and current contracts file
        keep_set = set([
            os.path.join('output', 'options_up_200_percent_latest.json'),
            os.path.join('output', 'watcher_status.json'),
            os.path.join('output', 'scheduler_config.json'),
            os.path.join('output', 'current_month_nfo_contracts.txt'),
        ])
        to_delete_files = [p for p in to_delete_files if p not in keep_set]

        # Logs folder contents
        log_files = []
        if os.path.isdir('logs'):
            for root, _, files in os.walk('logs'):
                for f in files:
                    log_files.append(os.path.join(root, f))
        to_delete_files.extend(log_files)

        # Python caches and pyc
        pyc_files = []
        pycache_dirs = []
        for root, dirs, files in os.walk('.'):
            for f in files:
                if f.endswith('.pyc'):
                    pyc_files.append(os.path.join(root, f))
            for d in list(dirs):
                if d == '__pycache__':
                    pycache_dirs.append(os.path.join(root, d))
        to_delete_files.extend(pyc_files)

        # Summary
        unique_files = sorted(set(to_delete_files))
        print(f"Found {len(unique_files)} files to delete.")
        preview = unique_files[:20]
        for p in preview:
            print(f"  - {p}")
        if len(unique_files) > len(preview):
            print(f"  ... and {len(unique_files) - len(preview)} more")

        confirm = input("\nProceed with deletion? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Cleanup cancelled.")
            return

        # Delete files
        deleted = 0
        for p in unique_files:
            try:
                if os.path.isfile(p):
                    os.remove(p)
                    deleted += 1
            except Exception as e:
                print(f"⚠️  Could not delete {p}: {e}")

        # Delete __pycache__ dirs
        removed_dirs = 0
        for d in pycache_dirs:
            try:
                shutil.rmtree(d, ignore_errors=True)
                removed_dirs += 1
            except Exception:
                pass

        print(f"✅ Cleanup complete. Deleted {deleted} files and removed {removed_dirs} __pycache__ directories.")
    
    def handle_refresh_session(self, kite) -> bool:
        """
        Handle session refresh
        
        Args:
            kite: KiteConnect instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        print("\n" + "="*70)
        print("REFRESHING SESSION")
        print("="*70)
        
        success, message = self.auth_service.refresh_session(kite)
        if success:
            print("✅ Session refreshed successfully!")
            return True
        else:
            print("❌ Failed to refresh session!")
            return False
    
    def save_contracts_to_file(self, filename: str = "current_month_nfo_contracts.txt") -> bool:
        """
        Save current month contracts to text file
        
        Args:
            filename: Output filename
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure output directory exists
            os.makedirs('output', exist_ok=True)
            output_path = os.path.join('output', filename)
            
            print(f"\n🔄 Saving contracts to {output_path}...")
            
            with open(output_path, 'w', encoding='utf-8') as txtfile:
                txtfile.write("="*100 + "\n")
                txtfile.write("CURRENT MONTH NFO CONTRACTS - FUTURES AND OPTIONS\n")
                txtfile.write("="*100 + "\n")
                txtfile.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                
                summary = self.nfo_service.get_contract_summary()
                txtfile.write(f"Current Month: {summary['current_month']}\n")
                txtfile.write(f"Total Futures: {summary['total_futures']}\n")
                txtfile.write(f"Total Options: {summary['total_options']}\n")
                txtfile.write("="*100 + "\n\n")
                
                # Summary by underlying
                underlyings = sorted(set([inst.get('name', '') for inst in self.nfo_service.current_month_futures + self.nfo_service.current_month_options]))
                
                # Load NFO list for comparison
                nfo_stocks_list = self.nfo_service.load_nfo_list()
                nfo_stocks_upper = [stock.upper() for stock in nfo_stocks_list]
                
                txtfile.write("SUMMARY BY UNDERLYING:\n")
                txtfile.write("-" * 60 + "\n")
                txtfile.write(f"{'Underlying':<20} {'Futures':<8} {'Options':<8} {'Total':<8}\n")
                txtfile.write("-" * 60 + "\n")
                
                for underlying in underlyings:
                    if underlying:
                        futures_count = len([f for f in self.nfo_service.current_month_futures if f.get('name', '').upper() == underlying.upper()])
                        options_count = len([o for o in self.nfo_service.current_month_options if o.get('name', '').upper() == underlying.upper()])
                        total = futures_count + options_count
                        txtfile.write(f"{underlying:<20} {futures_count:<8} {options_count:<8} {total:<8}\n")
                
                # Coverage summary
                if nfo_stocks_upper:
                    txtfile.write(f"\nCOVERAGE SUMMARY:\n")
                    txtfile.write("-" * 60 + "\n")
                    found_stocks = set([inst.get('name', '').upper() for inst in self.nfo_service.current_month_futures + self.nfo_service.current_month_options])
                    missing_stocks = set(nfo_stocks_upper) - found_stocks
                    
                    txtfile.write(f"Total stocks in NFO list: {len(nfo_stocks_upper)}\n")
                    txtfile.write(f"Stocks with contracts found: {len(found_stocks)}\n")
                    txtfile.write(f"Stocks missing contracts: {len(missing_stocks)}\n")
                    txtfile.write(f"Coverage: {len(found_stocks)/len(nfo_stocks_upper)*100:.1f}%\n")
                    
                    if missing_stocks:
                        txtfile.write(f"\nMissing stocks:\n")
                        for stock in sorted(missing_stocks):
                            txtfile.write(f"  - {stock}\n")
                
                # Futures section
                txtfile.write("\n" + "="*120 + "\n")
                txtfile.write("CURRENT MONTH FUTURES CONTRACTS\n")
                txtfile.write("="*120 + "\n")
                txtfile.write(f"{'Symbol':<25} {'Name':<15} {'Expiry':<12} {'Lot Size':<8} {'LTP':<8} {'Close':<8} {'Change%':<8} {'Volume':<10}\n")
                txtfile.write("-" * 120 + "\n")
                
                for future in sorted(self.nfo_service.current_month_futures, key=lambda x: x.get('name', '')):
                    symbol = future.get('tradingsymbol', 'N/A')
                    name = future.get('name', 'N/A')
                    expiry = future.get('expiry', 'N/A')
                    lot_size = future.get('lot_size', 0)
                    ltp = future.get('last_price', 0)
                    close = future.get('close_price', 0)
                    change_percent = future.get('change_percent', 0)
                    volume = future.get('volume', 0)
                    txtfile.write(f"{symbol:<25} {name:<15} {expiry:<12} {lot_size:<8} {ltp:<8} {close:<8} {change_percent:<8} {volume:<10}\n")
                
                # Options section
                txtfile.write("\n" + "="*130 + "\n")
                txtfile.write("CURRENT MONTH OPTIONS CONTRACTS (ATM + OTM)\n")
                txtfile.write("="*130 + "\n")
                txtfile.write(f"{'Symbol':<30} {'Name':<15} {'Type':<4} {'Strike':<8} {'LTP':<8} {'Close':<8} {'Change%':<8} {'Volume':<10}\n")
                txtfile.write("-" * 130 + "\n")
                
                for option in sorted(self.nfo_service.current_month_options, key=lambda x: (x.get('name', ''), x.get('strike', 0))):
                    symbol = option.get('tradingsymbol', 'N/A')
                    name = option.get('name', 'N/A')
                    instrument_type = option.get('instrument_type', 'N/A')
                    strike = option.get('strike', 0)
                    ltp = option.get('last_price', 0)
                    close = option.get('close_price', 0)
                    change_percent = option.get('change_percent', 0)
                    volume = option.get('volume', 0)
                    txtfile.write(f"{symbol:<30} {name:<15} {instrument_type:<4} {strike:<8} {ltp:<8} {close:<8} {change_percent:<8} {volume:<10}\n")
                
                txtfile.write("\n" + "="*100 + "\n")
                txtfile.write("END OF CURRENT MONTH NFO CONTRACTS\n")
                txtfile.write("="*100 + "\n")
            
            print(f"✅ Saved contracts to {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save file: {e}")
            return False
    
    def save_options_up_percentage_to_file(self, options_up_percentage: List[Dict], filename: str) -> bool:
        """
        Save options up percentage results to file
        
        Args:
            options_up_percentage: List of options meeting criteria
            filename: Output filename
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure output directory exists
            os.makedirs('output', exist_ok=True)
            output_path = os.path.join('output', filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("="*100 + "\n")
                f.write("OPTIONS UP 200% OR MORE\n")
                f.write("="*100 + "\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Options Found: {len(options_up_percentage)}\n")
                f.write("="*100 + "\n\n")
                
                f.write(f"{'Symbol':<30} {'Name':<15} {'Type':<4} {'Strike':<8} {'Open':<8} {'Current':<8} {'Change %':<10} {'Volume':<10}\n")
                f.write("-" * 100 + "\n")
                
                for item in options_up_percentage:
                    option = item['option']
                    symbol = option.get('tradingsymbol', 'N/A')
                    name = option.get('name', 'N/A')
                    inst_type = option.get('instrument_type', 'N/A')
                    strike = option.get('strike', 0)
                    open_price = item['open_price']
                    current_price = item['current_price']
                    percentage_change = item['percentage_change']
                    volume = item['quote_data'].get('volume', 0)
                    
                    f.write(f"{symbol:<30} {name:<15} {inst_type:<4} {strike:<8} {open_price:<8} {current_price:<8} {percentage_change:<10.2f} {volume:<10}\n")
                
                f.write("\n" + "="*100 + "\n")
                f.write("END OF OPTIONS UP 200% OR MORE\n")
                f.write("="*100 + "\n")
            
            print(f"\n📁 Results saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"⚠️  Could not save to file: {e}")
            return False
