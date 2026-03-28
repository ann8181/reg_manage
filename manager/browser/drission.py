"""
DrissionPage Browser Adapter
"""

from typing import Dict, Optional, Any
from DrissionPage import ChromiumPage, ChromiumOptions


class DrissionBrowser:
    def __init__(self, config):
        self.config = config
        self._page: Optional[ChromiumPage] = None
        self._browser = None
    
    def launch(self) -> "DrissionBrowser":
        opts = ChromiumOptions()
        
        if self.config.headless:
            opts.set_argument("--headless")
        
        if self.config.proxy:
            opts.set_proxy(self.config.proxy)
        
        if self.config.executable_path:
            opts.set_browser_path(self.config.executable_path)
        
        if self.config.window_size:
            width, height = map(int, self.config.window_size.split(","))
            opts.set_argument(f"--window-size={width},{height}")
        
        if self.config.user_data_dir:
            opts.set_user_data_path(self.config.user_data_dir)
        
        if self.config.profile_dir:
            opts.set_profile_path(self.config.profile_dir)
        
        opts.set_argument("--disable-blink-features=AutomationControlled")
        opts.set_argument("--no-sandbox")
        
        self._page = ChromiumPage(addr_or_opts=opts)
        return self
    
    def new_page(self):
        if not self._page:
            self.launch()
        return self._page.new_tab() if hasattr(self._page, 'new_tab') else self._page
    
    def _apply_stealth(self):
        if self._page and self.config.css_stealth:
            self._page.set.headers({
                "Accept-Language": "en-US,en;q=0.9"
            })
    
    def close(self):
        if self._page:
            try:
                self._page.quit()
            except Exception:
                pass
    
    def __enter__(self):
        return self.launch()
    
    def __exit__(self, *args):
        self.close()
