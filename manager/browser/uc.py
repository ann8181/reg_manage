"""
Undetected Chrome Browser Adapter
"""

from typing import Dict, Optional, Any
import undetected_chromedriver as uc


class UndetectedChromeBrowser:
    def __init__(self, config):
        self.config = config
        self._driver = None
        self._page = None
    
    def launch(self) -> "UndetectedChromeBrowser":
        opts = uc.ChromeOptions()
        
        if self.config.headless:
            opts.add_argument("--headless")
        
        if self.config.proxy:
            opts.add_argument(f"--proxy-server={self.config.proxy}")
        
        if self.config.executable_path:
            opts.binary_location = self.config.executable_path
        
        if self.config.window_size:
            width, height = map(int, self.config.window_size.split(","))
            opts.add_argument(f"--window-size={width},{height}")
        
        if self.config.extensions:
            for ext in self.config.extensions:
                opts.add_extension(ext)
        
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        
        self._driver = uc.Chrome(options=opts, version_main=self.config.version or None)
        return self
    
    def new_page(self):
        if self._driver:
            self._page = self._driver.new_tab() if hasattr(self._driver, 'new_tab') else self._driver
            self._apply_stealth()
            return self._page
        return None
    
    def _apply_stealth(self):
        if self._page and hasattr(self._page, 'execute_script'):
            self._page.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def close(self):
        if self._driver:
            try:
                self._driver.quit()
            except Exception:
                pass
    
    def __enter__(self):
        return self.launch()
    
    def __exit__(self, *args):
        self.close()
