"""
Browser Manager - 多浏览器统一管理
"""

import uuid
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import yaml
import os


logger = logging.getLogger(__name__)


class BrowserType(Enum):
    CAMOUFOX = "camoufox"           # 过CF首选
    UNDETECTED = "undetected"      # undetected-chromedriver
    DRISSION = "drission"          # DrissionPage
    PLAYWRIGHT = "playwright"       # Playwright
    PUPPETEER = "puppeteer"        # Puppeteer


@dataclass
class BrowserConfig:
    id: str
    name: str
    browser_type: BrowserType
    version: str = ""
    headless: bool = True
    
    # 浏览器路径
    executable_path: str = ""
    
    # 代理配置
    proxy: str = ""
    proxy_auth: str = ""
    
    # 反检测配置
    disable_webdriver: bool = True
    hide_chrome: bool = True
    randomize_user_agent: bool = True
    
    # 窗口配置
    window_size: str = "1920,1080"
    window_position: str = "0,0"
    
    # 其他配置
    extensions: List[str] = field(default_factory=list)
    user_data_dir: str = ""
    profile_dir: str = ""
    
    # 自动化配置
    auto_port: int = 0              # 自动化端口
    load_images: bool = True
    css_stealth: bool = True
    js_stealth: bool = True
    
    # 标签页配置
    max_tabs: int = 5
    
    # 指纹配置
    fingerprint: Dict[str, Any] = field(default_factory=dict)
    
    enabled: bool = True
    priority: int = 0
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]


class BrowserManager:
    """
    多浏览器统一管理器
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        self.configs: Dict[str, BrowserConfig] = {}
        self.instances: Dict[str, Any] = {}
        self.active_browsers: Dict[str, Any] = {}
        
        self.config_dir = "data/browser_configs"
        os.makedirs(self.config_dir, exist_ok=True)
        
        self._load_configs()
        logger.info("BrowserManager initialized")
    
    def _load_configs(self):
        """加载浏览器配置"""
        config_file = os.path.join(self.config_dir, "browsers.yaml")
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f)
                for cfg in data.get("browsers", []):
                    browser_type = BrowserType(cfg.get("browser_type", "camoufox"))
                    cfg["browser_type"] = browser_type
                    self.configs[cfg["id"]] = BrowserConfig(**cfg)
        
        # 添加默认配置
        if not self.configs:
            self._add_default_configs()
    
    def _add_default_configs(self):
        """添加默认浏览器配置"""
        defaults = [
            BrowserConfig(
                id="cf-stealth",
                name="CF Stealth (Camoufox)",
                browser_type=BrowserType.CAMOUFOX,
                version="latest",
                css_stealth=True,
                js_stealth=True,
                hide_chrome=True,
                disable_webdriver=True,
                priority=100
            ),
            BrowserConfig(
                id="uc-standard",
                name="Undetected Chrome",
                browser_type=BrowserType.UNDETECTED,
                version="latest",
                priority=80
            ),
            BrowserConfig(
                id="drission-adaptive",
                name="DrissionPage Adaptive",
                browser_type=BrowserType.DRISSION,
                version="latest",
                priority=60
            ),
            BrowserConfig(
                id="playwright-chrome",
                name="Playwright Chrome",
                browser_type=BrowserType.PLAYWRIGHT,
                version="latest",
                priority=40
            )
        ]
        
        for cfg in defaults:
            self.configs[cfg.id] = cfg
        
        self.save_configs()
    
    def save_configs(self):
        """保存配置"""
        config_file = os.path.join(self.config_dir, "browsers.yaml")
        data = {
            "browsers": [
                {
                    **vars(cfg),
                    "browser_type": cfg.browser_type.value
                }
                for cfg in self.configs.values()
            ]
        }
        with open(config_file, 'w') as f:
            yaml.dump(data, f)
    
    def add_config(self, config: BrowserConfig) -> BrowserConfig:
        """添加浏览器配置"""
        self.configs[config.id] = config
        self.save_configs()
        return config
    
    def get_config(self, config_id: str) -> Optional[BrowserConfig]:
        return self.configs.get(config_id)
    
    def list_configs(self) -> List[BrowserConfig]:
        return sorted(self.configs.values(), key=lambda x: x.priority, reverse=True)
    
    def get_best_config(self, service: str = None) -> Optional[BrowserConfig]:
        """获取最佳浏览器配置"""
        configs = self.list_configs()
        if service:
            # 根据服务类型选择
            service_preferences = {
                "outlook": ["camoufox", "undetected"],
                "github": ["camoufox", "drission"],
                "gpt": ["camoufox", "playwright"],
                "claude": ["camoufox", "undetected"],
            }
            preferred = service_preferences.get(service.lower(), [])
            for pref in preferred:
                for cfg in configs:
                    if pref in cfg.browser_type.value:
                        return cfg
        
        # 返回最高优先级
        return configs[0] if configs else None
    
    def create_browser(self, config_id: str = None, service: str = None) -> Optional[Any]:
        """创建浏览器实例"""
        if not config_id:
            config = self.get_best_config(service)
        else:
            config = self.get_config(config_id)
        
        if not config:
            logger.error(f"No browser config found for {config_id or service}")
            return None
        
        try:
            if config.browser_type == BrowserType.CAMOUFOX:
                from .camoufox import CamoufoxBrowser
                browser = CamoufoxBrowser(config)
            elif config.browser_type == BrowserType.UNDETECTED:
                from .uc import UndetectedChromeBrowser
                browser = UndetectedChromeBrowser(config)
            elif config.browser_type == BrowserType.DRISSION:
                from .drission import DrissionBrowser
                browser = DrissionBrowser(config)
            elif config.browser_type == BrowserType.PLAYWRIGHT:
                from playwright.sync_api import sync_playwright
                browser = sync_playwright().start().chromium.launch(headless=config.headless)
            else:
                return None
            
            self.active_browsers[config.id] = browser
            logger.info(f"Created browser: {config.name}")
            return browser
            
        except Exception as e:
            logger.error(f"Failed to create browser {config_id}: {e}")
            return None
    
    def close_browser(self, config_id: str):
        """关闭浏览器"""
        if config_id in self.active_browsers:
            try:
                browser = self.active_browsers[config_id]
                if hasattr(browser, 'close'):
                    browser.close()
                elif hasattr(browser, 'stop'):
                    browser.stop()
                del self.active_browsers[config_id]
            except Exception as e:
                logger.error(f"Error closing browser {config_id}: {e}")
    
    def close_all(self):
        """关闭所有浏览器"""
        for config_id in list(self.active_browsers.keys()):
            self.close_browser(config_id)
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_configs": len(self.configs),
            "active_browsers": len(self.active_browsers),
            "configs": [
                {
                    "id": c.id,
                    "name": c.name,
                    "type": c.browser_type.value,
                    "enabled": c.enabled,
                    "priority": c.priority
                }
                for c in self.list_configs()
            ]
        }


def get_browser_manager() -> BrowserManager:
    return BrowserManager()
