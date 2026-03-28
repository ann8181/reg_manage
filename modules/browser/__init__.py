"""
Browser Module - 浏览器管理模块
支持多浏览器注册到内核
"""

import uuid
from typing import Dict, List, Optional, Any


class BrowserType:
    CAMOUFOX = "camoufox"
    UNDETECTED = "undetected"
    DRISSION = "drission"
    PLAYWRIGHT = "playwright"


class BrowserConfig:
    """浏览器配置"""
    
    def __init__(
        self,
        id: str = None,
        name: str = "",
        browser_type: str = BrowserType.CAMOUFOX,
        headless: bool = True,
        proxy: str = "",
        **kwargs
    ):
        self.id = id or str(uuid.uuid4())[:8]
        self.name = name
        self.browser_type = browser_type
        self.headless = headless
        self.proxy = proxy
        self.enabled = True
        self.priority = kwargs.get("priority", 0)
        
        # 隐身配置
        self.css_stealth = kwargs.get("css_stealth", True)
        self.js_stealth = kwargs.get("js_stealth", True)
        self.hide_chrome = kwargs.get("hide_chrome", True)
        
        # 窗口配置
        self.window_size = kwargs.get("window_size", "1920,1080")
        
        # 服务偏好
        self.services = kwargs.get("services", [])
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "browser_type": self.browser_type,
            "headless": self.headless,
            "proxy": self.proxy,
            "enabled": self.enabled,
            "priority": self.priority,
            "css_stealth": self.css_stealth,
            "js_stealth": self.js_stealth,
            "window_size": self.window_size,
            "services": self.services
        }


class BrowserModule:
    """
    浏览器管理模块
    负责浏览器的配置管理和实例化
    """
    
    def __init__(self, kernel):
        self.kernel = kernel
        self.configs: Dict[str, BrowserConfig] = {}
        self.instances: Dict[str, Any] = {}
        self.logger = kernel.get_logger("browser")
        
        # 注册默认配置
        self._register_defaults()
        
        self.logger.info("BrowserModule initialized")
    
    def _register_defaults(self):
        """注册默认浏览器配置"""
        defaults = [
            BrowserConfig(
                id="camoufox-stealth",
                name="Camoufox Stealth",
                browser_type=BrowserType.CAMOUFOX,
                headless=True,
                css_stealth=True,
                js_stealth=True,
                hide_chrome=True,
                priority=100,
                services=["outlook", "github", "claude", "gpt"]
            ),
            BrowserConfig(
                id="uc-standard",
                name="Undetected Chrome",
                browser_type=BrowserType.UNDETECTED,
                priority=80,
                services=["openai", "gemini"]
            ),
            BrowserConfig(
                id="playwright-chrome",
                name="Playwright Chrome",
                browser_type=BrowserType.PLAYWRIGHT,
                priority=60
            )
        ]
        
        for cfg in defaults:
            self.configs[cfg.id] = cfg
    
    def add_config(self, config: BrowserConfig) -> BrowserConfig:
        """添加浏览器配置"""
        self.configs[config.id] = config
        self.logger.info(f"Browser config added: {config.name}")
        return config
    
    def get_config(self, config_id: str) -> Optional[BrowserConfig]:
        return self.configs.get(config_id)
    
    def remove_config(self, config_id: str):
        if config_id in self.configs:
            del self.configs[config_id]
    
    def list_configs(self) -> List[BrowserConfig]:
        return sorted(self.configs.values(), key=lambda x: x.priority, reverse=True)
    
    def get_best_for(self, service: str) -> Optional[BrowserConfig]:
        """为服务获取最佳浏览器"""
        configs = self.list_configs()
        
        # 优先选择支持该服务的配置
        for cfg in configs:
            if cfg.enabled and service.lower() in [s.lower() for s in cfg.services]:
                return cfg
        
        # 返回最高优先级
        return configs[0] if configs else None
    
    def create_browser(self, config_id: str = None, service: str = None):
        """创建浏览器实例"""
        if config_id:
            config = self.get_config(config_id)
        elif service:
            config = self.get_best_for(service)
        else:
            configs = self.list_configs()
            config = configs[0] if configs else None
        
        if not config:
            raise ValueError("No browser config found")
        
        try:
            if config.browser_type == BrowserType.CAMOUFOX:
                from camoufox.sync_api import Camoufox
                
                opts = {"headless": config.headless, "antibot": True}
                
                if config.proxy:
                    opts["proxy"] = config.proxy
                
                width, height = config.window_size.split(",")
                opts["viewport"] = {"width": int(width), "height": int(height)}
                
                browser = Camoufox(**opts)
                page = browser.new_page()
                
                self.instances[config.id] = {"browser": browser, "page": page}
                
                self.logger.info(f"Browser created: {config.name}")
                return page
            
            elif config.browser_type == BrowserType.PLAYWRIGHT:
                from playwright.sync_api import sync_playwright
                
                p = sync_playwright().start()
                browser = p.chromium.launch(headless=config.headless)
                page = browser.new_page()
                
                self.instances[config.id] = {"playwright": p, "browser": browser, "page": page}
                
                return page
            
            else:
                raise NotImplementedError(f"Browser type {config.browser_type} not implemented")
        
        except Exception as e:
            self.logger.error(f"Failed to create browser: {e}")
            raise
    
    def close_browser(self, config_id: str):
        """关闭浏览器"""
        if config_id in self.instances:
            instance = self.instances[config_id]
            
            if "page" in instance:
                try:
                    instance["page"].close()
                except:
                    pass
            
            if "browser" in instance:
                try:
                    instance["browser"].close()
                except:
                    pass
            
            if "playwright" in instance:
                try:
                    instance["playwright"].stop()
                except:
                    pass
            
            del self.instances[config_id]
            self.logger.info(f"Browser closed: {config_id}")
    
    def close_all(self):
        """关闭所有浏览器"""
        for config_id in list(self.instances.keys()):
            self.close_browser(config_id)
    
    def get_stats(self) -> Dict:
        return {
            "total_configs": len(self.configs),
            "active_instances": len(self.instances)
        }
    
    def stop(self):
        """停止模块"""
        self.close_all()
        self.logger.info("BrowserModule stopped")
