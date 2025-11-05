#!/usr/bin/env python3
"""
Scheduled watcher: Every 5 minutes executes Option 1 (fetch contracts) then Option 8 (options up 200%).
If the Option 8 result changes versus the previous run, alert the user and write a diff file.

Usage:
  python watch_options_changes.py            # runs indefinitely (Ctrl+C to stop)
  python watch_options_changes.py --once     # runs a single cycle (for testing)
  python watch_options_changes.py --interval 600  # custom interval seconds
"""

import sys
import os
import time
import json
from datetime import datetime

# Ensure src is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from kite_trader.core.app import KiteTraderApp
from kite_trader.core.app_config import AppConfig

# Notification backends (optional)
_notifier = None
_notify_backend = None
try:
    from win10toast import ToastNotifier  # Windows native
    _notifier = ToastNotifier()
    _notify_backend = 'win10toast'
except Exception:
    try:
        from plyer import notification  # Cross-platform fallback
        _notify_backend = 'plyer'
    except Exception:
        _notify_backend = None


def serialize_options_up(options_up_list):
    """Return a stable list of unique script names (underlying names) for change detection."""
    names: set = set()
    for item in options_up_list or []:
        opt = item.get('option', {})
        name = (opt.get('name') or '').strip()
        # Fallback to tradingsymbol if name missing
        if not name:
            name = (opt.get('tradingsymbol') or '').strip()
        if name:
            names.add(name.upper())
    # Deterministic order
    return sorted(names)


def load_previous(path):
    """Load previous snapshot and normalize to a sorted list of upper-case script names."""
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # If legacy format (list of dicts), migrate to names
            if isinstance(data, list) and data:
                if isinstance(data[0], dict):
                    names = set()
                    for item in data:
                        name = (item.get('name') if isinstance(item, dict) else '') or ''
                        if not name and isinstance(item, dict):
                            name = (item.get('tradingsymbol') or '').strip()
                        if name:
                            names.add(name.upper())
                    return sorted(names)
                elif isinstance(data[0], str):
                    return sorted({s.upper() for s in data if isinstance(s, str) and s.strip()})
            return []
    except Exception:
        pass
    return []


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def ensure_scheduler_config(config_path: str) -> dict:
    """Load or create a scheduler config file."""
    # Pull defaults from AppConfig if present
    app_cfg = AppConfig().get_scheduler()
    default_cfg = {
        "interval_seconds": int(app_cfg.get("interval_seconds", 300)),
        "notify_on_change": bool(app_cfg.get("notify_on_change", True)),
        "notify_always": bool(app_cfg.get("notify_always", False)),
        "notification_title": app_cfg.get("notification_title", "Options Up 200% Changed"),
        "notification_duration": int(app_cfg.get("notification_duration", 5))
    }
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            # Fill missing keys with defaults
            for k, v in default_cfg.items():
                cfg.setdefault(k, v)
            return cfg
        except Exception:
            pass
    # Create default
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(default_cfg, f, indent=2)
    return default_cfg


def send_notification(title: str, message: str, duration: int = 5):
    """Send a desktop notification if supported; otherwise print/beep."""
    try:
        if _notify_backend == 'win10toast' and _notifier is not None:
            # Use non-threaded mode to avoid WNDPROC/LPARAM issues on some setups
            _notifier.show_toast(title or "Notification", message or "", duration=duration, threaded=False)
            return
        if _notify_backend == 'plyer':
            notification.notify(title=title or "Notification", message=message or "", timeout=duration)
            return
    except Exception:
        # Fallback to alternate backend if available
        try:
            if _notify_backend != 'plyer':
                from plyer import notification as _n
                _n.notify(title=title or "Notification", message=message or "", timeout=duration)
                return
        except Exception:
            pass
    # Fallback
    try:
        print('\a')  # bell
    except Exception:
        pass
    print(f"[NOTIFY] {title}: {message}")


def diff_lists(prev_list, curr_list):
    """Compare only by script name. Return added names; removals ignored for alerting."""
    prev_set = set(prev_list)
    curr_set = set(curr_list)
    added = sorted(curr_set - prev_set)
    removed = sorted(prev_set - curr_set)
    return added, removed


def run_cycle(app: KiteTraderApp, previous_path: str):
    # Ensure authenticated
    if not app.is_authenticated:
        if not app.authenticate():
            print('❌ Authentication failed; retrying next cycle...')
            return None

    # Option 1: fetch current month NFO contracts (full refresh pipeline)
    if not app.menu_service.handle_fetch_contracts(app.kite):
        print('❌ Option 1 failed; retrying next cycle...')
        return None

    # Option 8 core: compute options up 200% (use service directly to capture results)
    options_up = app.market_data_service.find_options_up_percentage(app.kite, app.nfo_service, 200.0)

    # Persist a stable, comparable snapshot
    curr_stable = serialize_options_up(options_up)
    save_json(previous_path, curr_stable)

    return curr_stable


def main():
    # Load config
    config_path = os.path.join('output', 'scheduler_config.json')
    cfg = ensure_scheduler_config(config_path)

    # CLI overrides
    interval_seconds = cfg.get('interval_seconds', 300)
    if '--interval' in sys.argv:
        try:
            idx = sys.argv.index('--interval')
            interval_seconds = int(sys.argv[idx + 1])
        except Exception:
            print('⚠️  Invalid --interval value, using configured/default')
    notify_on_change = cfg.get('notify_on_change', True)
    notify_always = cfg.get('notify_always', False)
    notification_title = cfg.get('notification_title', 'Options Up 200% Changed')
    notification_duration = int(cfg.get('notification_duration', 5))

    run_once = '--once' in sys.argv

    app = KiteTraderApp()
    output_dir = os.path.join('output')
    latest_json = os.path.join(output_dir, 'options_up_200_percent_latest.json')
    status_json = os.path.join(output_dir, 'watcher_status.json')

    prev_snapshot = load_previous(latest_json)
    print('🔄 Starting watcher; interval:', interval_seconds, 'seconds')

    while True:
        start = datetime.now()
        print('\n' + '='*70)
        print('RUN @', start.strftime('%Y-%m-%d %H:%M:%S'))
        print('='*70)

        curr_snapshot = run_cycle(app, latest_json)
        if curr_snapshot is not None:
            added, removed = diff_lists(prev_snapshot, curr_snapshot)
            # Alert only when new scripts are added
            if added:
                # Alert
                print('\a')  # System bell (may beep on terminals)
                print('🚨 New scripts detected in Option 8 results!')
                print(f'   Added scripts: {len(added)}')

                if notify_on_change:
                    send_notification(
                        notification_title,
                        f"Added scripts: {len(added)}",
                        notification_duration
                    )

                # Save detailed diff
                ts = start.strftime('%Y%m%d_%H%M%S')
                diff_path = os.path.join(output_dir, f'options_up_diff_{ts}.txt')
                os.makedirs(output_dir, exist_ok=True)
                with open(diff_path, 'w', encoding='utf-8') as f:
                    f.write(f'DIFF @ {start}\n')
                    f.write(f'Added scripts ({len(added)}):\n')
                    for name in added:
                        f.write(f'  + {name}\n')
                print('📝 Diff saved to:', diff_path)

                # Update previous snapshot
                prev_snapshot = curr_snapshot
            else:
                print('✅ No change since last run.')
                if notify_always:
                    send_notification(
                        'Options Up 200% Watcher',
                        'No change since last run',
                        max(3, notification_duration - 1)
                    )

            # Update status file
            try:
                next_run_eta = start.timestamp() + interval_seconds
                status = {
                    'last_run': start.strftime('%Y-%m-%d %H:%M:%S'),
                    'interval_seconds': interval_seconds,
                    'added_count': len(added) if curr_snapshot is not None else None,
                    'removed_count': len(removed) if curr_snapshot is not None else None,
                    'next_run_eta': int(next_run_eta),
                }
                save_json(status_json, status)
            except Exception:
                pass

        # End or sleep
        if run_once:
            break

        elapsed = (datetime.now() - start).total_seconds()
        sleep_for = max(0, interval_seconds - int(elapsed))
        print(f'⏳ Sleeping {sleep_for}s... | Last run: {start.strftime('%Y-%m-%d %H:%M:%S')}')
        time.sleep(sleep_for)


if __name__ == '__main__':
    try:
        # Quick test path for notifications: --notify-test [title] [message]
        if '--notify-test' in sys.argv:
            idx = sys.argv.index('--notify-test')
            title = 'Options Up 200% Watcher'
            message = 'This is a test notification.'
            if len(sys.argv) > idx + 1:
                title = sys.argv[idx + 1]
            if len(sys.argv) > idx + 2:
                message = sys.argv[idx + 2]
            send_notification(title, message, 5)
        else:
            main()
    except KeyboardInterrupt:
        print('\n👋 Stopped watcher.')

