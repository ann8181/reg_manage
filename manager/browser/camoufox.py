"""
Camoufox Browser Adapter - 过CF专用
"""

from typing import Dict, Optional, Any
from camoufox.sync_api import Camoufox


class CamoufoxBrowser:
    def __init__(self, config):
        self.config = config
        self._browser = None
        self._page = None
    
    def launch(self) -> "CamoufoxBrowser":
        opts = {
            "headless": self.config.headless,
            "antibot": True,
            "auto_clone": True,
        }
        
        if self.config.proxy:
            opts["proxy"] = self.config.proxy
        
        if self.config.executable_path:
            opts["executable_path"] = self.config.executable_path
        
        if self.config.window_size:
            width, height = map(int, self.config.window_size.split(","))
            opts["viewport"] = {"width": width, "height": height}
        
        self._browser = Camoufox(**opts)
        return self
    
    def new_page(self):
        self._page = self._browser.new_page()
        self._apply_stealth()
        return self._page
    
    def _apply_stealth(self):
        if self._page:
            if self.config.css_stealth:
                self._page.set_extra_http_headers({
                    "Accept-Language": "en-US,en;q=0.9"
                })
    
    def close(self):
        if self._browser:
            self._browser.close()
    
    def __enter__(self):
        return self.launch()
    
    def __exit__(self, *args):
        self.close()
