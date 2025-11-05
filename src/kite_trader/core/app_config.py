#!/usr/bin/env python3
"""
Application Config Loader

Loads configuration from config/app_config.json with sane defaults.
"""

import os
import json
from typing import Any, Dict


class AppConfig:
    def __init__(self, path: str = os.path.join('config', 'app_config.json')):
        self.path = path
        self.config = self._load()

    def _defaults(self) -> Dict[str, Any]:
        return {
            "kite_timeout_seconds": 30,
            "nfo_list_path": "data/Nfo_List.txt",
            "month_override": "",  # e.g., "25OCT"; empty means auto
            "fallback_next_month": True,
            "options_filter_max_strikes": 5,
            "options_up_threshold_percent": 200.0,
            "scheduler": {
                "interval_seconds": 300,
                "notify_on_change": True,
                "notify_always": False,
                "notification_title": "Options Up 200% Changed",
                "notification_duration": 5
            },
            "comments": {
                "kite_timeout_seconds": "Affects src/kite_trader/core/app.py (initialize_kite_connection)",
                "nfo_list_path": "Affects src/kite_trader/services/nfo_service.py (load_nfo_list)",
                "month_override": "Affects src/kite_trader/services/nfo_service.py (__init__/_get_current_month)",
                "fallback_next_month": "Affects src/kite_trader/services/nfo_service.py (get_current_month_contracts)",
                "options_filter_max_strikes": "Affects src/kite_trader/services/nfo_service.py (filter_atm_otm_options)",
                "options_up_threshold_percent": "Affects src/kite_trader/ui/menu_service.py (handle_options_up_200_percent)",
                "scheduler": "Affects watch_options_changes.py (main/ensure_scheduler_config)"
            }
        }

    def _load(self) -> Dict[str, Any]:
        cfg = self._defaults()
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    user = json.load(f)
                # simple deep-merge for one nested level
                for k, v in user.items():
                    if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                        cfg[k].update(v)
                    else:
                        cfg[k] = v
            except Exception:
                pass
        else:
            # create directory and write defaults
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, indent=2)
        return cfg

    # Getters
    def get_timeout(self) -> int:
        return int(self.config.get("kite_timeout_seconds", 30))

    def get_nfo_list_path(self) -> str:
        return str(self.config.get("nfo_list_path", "data/Nfo_List.txt"))

    def get_month_override(self) -> str:
        return str(self.config.get("month_override", "")).strip()

    def is_fallback_next_month_enabled(self) -> bool:
        return bool(self.config.get("fallback_next_month", True))

    def get_options_filter_max_strikes(self) -> int:
        return int(self.config.get("options_filter_max_strikes", 5))

    def get_options_up_threshold_percent(self) -> float:
        return float(self.config.get("options_up_threshold_percent", 200.0))

    def get_scheduler(self) -> Dict[str, Any]:
        return dict(self.config.get("scheduler", {}))



