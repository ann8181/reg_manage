"""
Browser Manager - 多浏览器管理系统
支持 camoufox, undetected-chromedriver, DrissionPage, playwright 等
"""
from .manager import BrowserManager, BrowserConfig, BrowserType

try:
    from .camoufox import CamoufoxBrowser
except ImportError:
    CamoufoxBrowser = None

try:
    from .uc import UndetectedChromeBrowser
except ImportError:
    UndetectedChromeBrowser = None

try:
    from .drission import DrissionBrowser
except ImportError:
    DrissionBrowser = None

__all__ = [
    "BrowserManager", 
    "BrowserConfig", 
    "BrowserType",
    "CamoufoxBrowser",
    "UndetectedChromeBrowser", 
    "DrissionBrowser"
]
