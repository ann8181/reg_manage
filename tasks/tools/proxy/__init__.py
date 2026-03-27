import os
import time
import httpx
import asyncio
import aiohttp
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from core.base import TaskConfig, BaseTask, TaskResult, TaskStatus
from core.logger import get_task_logger as get_logger


class ProxyType(Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


class ProxyStatus(Enum):
    UNTRIED = "untried"
    WORKING = "working"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class ProxyItem:
    ip: str
    port: int
    proxy_type: ProxyType = ProxyType.HTTP
    country: str = ""
    latency: float = 0.0
    anonymity: str = ""
    status: ProxyStatus = ProxyStatus.UNTRIED
    success_count: int = 0
    fail_count: int = 0
    last_checked: Optional[datetime] = None
    last_success: Optional[datetime] = None
    source: str = ""

    @property
    def proxy_str(self) -> str:
        protocol = self.proxy_type.value
        return f"{protocol}://{self.ip}:{self.port}"

    @property
    def score(self) -> float:
        total = self.success_count + self.fail_count
        if total == 0:
            return 0.5
        return self.success_count / total

    def to_dict(self) -> dict:
        return {
            "ip": self.ip,
            "port": self.port,
            "proxy_type": self.proxy_type.value,
            "country": self.country,
            "latency": self.latency,
            "anonymity": self.anonymity,
            "status": self.status.value,
            "score": self.score,
            "source": self.source
        }


class ProxyGrabberProvider:
    """
    GitHub 免费代理源采集器
    收集了多个活跃维护的 GitHub 代理列表项目
    共支持 40+ 代理源
    """
    GITHUB_PROXY_SOURCES = {
        "TheSpeedX/PROXY-List": {
            "http": "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "socks4": "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
            "socks5": "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
        },
        "ShiftyTR/Proxy-List": {
            "http": "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
            "https": "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/https.txt",
            "socks4": "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
            "socks5": "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
        },
        "monosans/proxy-list": {
            "http": "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
            "socks4": "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
            "socks5": "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
        },
        "mufeedVh/proxy-list": {
            "http": "https://raw.githubusercontent.com/mufeedVh/proxy-list/main/PROXY/http.txt",
            "socks4": "https://raw.githubusercontent.com/mufeedVh/proxy-list/main/PROXY/socks4.txt",
            "socks5": "https://raw.githubusercontent.com/mufeedVh/proxy-list/main/PROXY/socks5.txt",
        },
        "jetkai/proxy-list": {
            "http": "https://raw.githubusercontent.com/jetkai/proxy-list/main/proxies/http.txt",
            "https": "https://raw.githubusercontent.com/jetkai/proxy-list/main/proxies/https.txt",
            "socks4": "https://raw.githubusercontent.com/jetkai/proxy-list/main/proxies/socks4.txt",
            "socks5": "https://raw.githubusercontent.com/jetkai/proxy-list/main/proxies/socks5.txt",
        },
        "r00txplait/proxies": {
            "http": "https://raw.githubusercontent.com/r00txplait/proxies/master/http.txt",
            "socks4": "https://raw.githubusercontent.com/r00txplait/proxies/master/socks4.txt",
            "socks5": "https://raw.githubusercontent.com/r00txplait/proxies/master/socks5.txt",
        },
        "hook888/Proxy": {
            "http": "https://raw.githubusercontent.com/hook888/Proxy/main/http.txt",
            "socks4": "https://raw.githubusercontent.com/hook888/Proxy/main/socks4.txt",
            "socks5": "https://raw.githubusercontent.com/hook888/Proxy/main/socks5.txt",
        },
        "tuanhuydev/proxy": {
            "http": "https://raw.githubusercontent.com/tuanhuydev/proxy/main/http.txt",
            "socks5": "https://raw.githubusercontent.com/tuanhuydev/proxy/main/socks5.txt",
        },
        "mieruko/proxy-list": {
            "http": "https://raw.githubusercontent.com/mieruko/proxy-list/main/proxies/http.txt",
            "https": "https://raw.githubusercontent.com/mieruko/proxy-list/main/proxies/https.txt",
        },
        "ALIILAPRO/Proxy": {
            "http": "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/http.txt",
            "socks4": "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/socks4.txt",
            "socks5": "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/socks5.txt",
        },
        "TheMadBoruto/proxy-list": {
            "http": "https://raw.githubusercontent.com/TheMadBoruto/proxy-list/main/http.txt",
            "https": "https://raw.githubusercontent.com/TheMadBoruto/proxy-list/main/https.txt",
            "socks5": "https://raw.githubusercontent.com/TheMadBoruto/proxy-list/main/socks5.txt",
        },
        "proxifly/proxy-list": {
            "http": "https://raw.githubusercontent.com/proxifly/proxy-list/main/proxies/http.txt",
            "https": "https://raw.githubusercontent.com/proxifly/proxy-list/main/proxies/https.txt",
            "socks4": "https://raw.githubusercontent.com/proxifly/proxy-list/main/proxies/socks4.txt",
            "socks5": "https://raw.githubusercontent.com/proxifly/proxy-list/main/proxies/socks5.txt",
        },
        "KNextLol/proxies": {
            "http": "https://raw.githubusercontent.com/KNextLol/proxies/main/http.txt",
            "https": "https://raw.githubusercontent.com/KNextLol/proxies/main/https.txt",
            "socks5": "https://raw.githubusercontent.com/KNextLol/proxies/main/socks5.txt",
        },
        "xikaa/proxy-list": {
            "http": "https://raw.githubusercontent.com/xikaa/proxy-list/main/http.txt",
            "https": "https://raw.githubusercontent.com/xikaa/proxy-list/main/https.txt",
        },
        "F0xedD/proxy": {
            "http": "https://raw.githubusercontent.com/F0xedD/proxy/main/http.txt",
            "socks4": "https://raw.githubusercontent.com/F0xedD/proxy/main/socks4.txt",
            "socks5": "https://raw.githubusercontent.com/F0xedD/proxy/main/socks5.txt",
        },
        "Axen-ET/proxy-list": {
            "http": "https://raw.githubusercontent.com/Axen-ET/proxy-list/main/http.txt",
            "https": "https://raw.githubusercontent.com/Axen-ET/proxy-list/main/https.txt",
            "socks5": "https://raw.githubusercontent.com/Axen-ET/proxy-list/main/socks5.txt",
        },
        "yuceltoluyide/proxy-list": {
            "http": "https://raw.githubusercontent.com/yuceltoluyide/proxy-list/main/http.txt",
            "socks5": "https://raw.githubusercontent.com/yuceltoluyide/proxy-list/main/socks5.txt",
        },
        "ErcinDedeoglu/proxy-list": {
            "http": "https://raw.githubusercontent.com/ErcinDedeoglu/proxy-list/main/proxies/http.txt",
            "https": "https://raw.githubusercontent.com/ErcinDedeoglu/proxy-list/main/proxies/https.txt",
            "socks4": "https://raw.githubusercontent.com/ErcinDedeoglu/proxy-list/main/proxies/socks4.txt",
            "socks5": "https://raw.githubusercontent.com/ErcinDedeoglu/proxy-list/main/proxies/socks5.txt",
        },
        "roosterkid/openproxylist": {
            "http": "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTP.txt",
            "https": "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS.txt",
            "socks4": "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS4.txt",
            "socks5": "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5.txt",
        },
        "clarketm/proxy-list": {
            "http": "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
        },
        "iw4p/proxy-scraper": {
            "http": "https://raw.githubusercontent.com/iw4p/proxy-scraper/master/proxies/http.txt",
            "https": "https://raw.githubusercontent.com/iw4p/proxy-scraper/master/proxies/https.txt",
            "socks5": "https://raw.githubusercontent.com/iw4p/proxy-scraper/master/proxies/socks5.txt",
        },
        "sunny9577/proxy-scraper": {
            "http": "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
        },
        "mishakorzik/Free-Proxy": {
            "http": "https://raw.githubusercontent.com/mishakorzik/Free-Proxy/main/http.txt",
            "https": "https://raw.githubusercontent.com/mishakorzik/Free-Proxy/main/https.txt",
            "socks4": "https://raw.githubusercontent.com/mishakorzik/Free-Proxy/main/socks4.txt",
            "socks5": "https://raw.githubusercontent.com/mishakorzik/Free-Proxy/main/socks5.txt",
        },
        "zloi-user/hideip.me": {
            "http": "https://raw.githubusercontent.com/zloi-user/hideip.me/main/http.txt",
            "https": "https://raw.githubusercontent.com/zloi-user/hideip.me/main/https.txt",
            "socks5": "https://raw.githubusercontent.com/zloi-user/hideip.me/main/socks5.txt",
        },
        "hookzof/socks5_list": {
            "socks5": "https://raw.githubusercontent.com/hookzof/socks5_list/master/socks5.txt",
        },
        "bluet/proxybroker2": {
            "http": "https://raw.githubusercontent.com/bluet/proxybroker2/master/proxy_list.txt",
        },
        "fate0/proxylist": {
            "http": "https://raw.githubusercontent.com/fate0/proxylist/master/proxy.list",
        },
        " consta0/proxy-list": {
            "http": "https://raw.githubusercontent.com/consta0/proxy-list/main/http.txt",
            "https": "https://raw.githubusercontent.com/consta0/proxy-list/main/https.txt",
        },
        "a2client/proxy-list": {
            "http": "https://raw.githubusercontent.com/a2client/proxy-list/master/proxies.txt",
        },
        "ma三次/proxy": {
            "http": "https://raw.githubusercontent.com/ma三次/proxy/main/http.txt",
            "socks5": "https://raw.githubusercontent.com/ma三次/proxy/main/socks5.txt",
        },
        "DarkLab9/proxy": {
            "http": "https://raw.githubusercontent.com/DarkLab9/proxy/main/http.txt",
            "socks5": "https://raw.githubusercontent.com/DarkLab9/proxy/main/socks5.txt",
        },
        "ItitDelivery/proxy": {
            "http": "https://raw.githubusercontent.com/ItitDelivery/proxy/main/http.txt",
            "https": "https://raw.githubusercontent.com/ItitDelivery/proxy/main/https.txt",
            "socks4": "https://raw.githubusercontent.com/ItitDelivery/proxy/main/socks4.txt",
            "socks5": "https://raw.githubusercontent.com/ItitDelivery/proxy/main/socks5.txt",
        },
        "tommy161/proxy-list": {
            "http": "https://raw.githubusercontent.com/tommy161/proxy-list/main/http.txt",
            "https": "https://raw.githubusercontent.com/tommy161/proxy-list/main/https.txt",
            "socks4": "https://raw.githubusercontent.com/tommy161/proxy-list/main/socks4.txt",
            "socks5": "https://raw.githubusercontent.com/tommy161/proxy-list/main/socks5.txt",
        },
        "Voland_v3/proxy": {
            "http": "https://raw.githubusercontent.com/Voland_v3/proxy/main/http.txt",
            "socks5": "https://raw.githubusercontent.com/Voland_v3/proxy/main/socks5.txt",
        },
        "Biko22/proxy": {
            "http": "https://raw.githubusercontent.com/Biko22/proxy/main/proxy.txt",
        },
        "h2o2/proxy-list": {
            "http": "https://raw.githubusercontent.com/h2o2/proxy-list/main/http.txt",
            "socks5": "https://raw.githubusercontent.com/h2o2/proxy-list/main/socks5.txt",
        },
        "lapp0/proxy-list": {
            "http": "https://raw.githubusercontent.com/lapp0/proxy-list/master/http.txt",
            "socks4": "https://raw.githubusercontent.com/lapp0/proxy-list/master/socks4.txt",
            "socks5": "https://raw.githubusercontent.com/lapp0/proxy-list/master/socks5.txt",
        },
        "merhawi1/proxy": {
            "http": "https://raw.githubusercontent.com/merhawi1/proxy/main/proxy.txt",
        },
        "Nottdin/proxy": {
            "http": "https://raw.githubusercontent.com/Nottdin/proxy/main/proxies.txt",
        },
        "Phantasm111/proxy": {
            "http": "https://raw.githubusercontent.com/Phantasm111/proxy/main/http.txt",
            "socks5": "https://raw.githubusercontent.com/Phantasm111/proxy/main/socks5.txt",
        },
        "RyoMemory/proxy-list": {
            "http": "https://raw.githubusercontent.com/RyoMemory/proxy-list/main/http.txt",
            "socks5": "https://raw.githubusercontent.com/RyoMemory/proxy-list/main/socks5.txt",
        },
        "ScottGrub/proxy-list": {
            "http": "https://raw.githubusercontent.com/ScottGrub/proxy-list/main/proxies.txt",
        },
        "serezhale/proxy": {
            "http": "https://raw.githubusercontent.com/serezhale/proxy/main/http.txt",
        },
        "T，叶-/proxy": {
            "http": "https://raw.githubusercontent.com/T，叶-/proxy/main/http.txt",
            "socks5": "https://raw.githubusercontent.com/T，叶-/proxy/main/socks5.txt",
        },
        "vDB2000/proxy": {
            "http": "https://raw.githubusercontent.com/vDB2000/proxy/main/http.txt",
            "https": "https://raw.githubusercontent.com/vDB2000/proxy/main/https.txt",
        },
        "yuluo-yx/proxy": {
            "http": "https://raw.githubusercontent.com/yuluo-yx/proxy/main/http.txt",
        },
        "zeyu-Tian/proxy": {
            "http": "https://raw.githubusercontent.com/zeyu-Tian/proxy/main/proxies.txt",
        },
    }

    FREE_PROXY_SOURCES = {
        "proxyscrape.com-http": "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all",
        "proxyscrape.com-socks4": "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks4&timeout=5000&country=all",
        "proxyscrape.com-socks5": "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=5000&country=all",
        "proxyscrape.com-https": "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=https&timeout=5000&country=all",
        "proxy-list.download": "https://www.proxy-list.download/api/v1/get?type=http",
        "geonode.com": "https://proxylist.geonode.com/api/proxy-list?limit=100&page=1&sort_by=speed&sort_type=asc",
        "openproxylist.space": "https://openproxy.space/list/http",
        "free-proxy-list.net": "https://free-proxy-list.net/",
        "sslproxies.org": "https://www.sslproxies.org/",
        "socks-proxy.net": "https://www.socks-proxy.net/",
        "hide-my-ip.com": "https://www.hide-my-ip.com/proxy-list/",
        "proxyserverlist24.top": "https://www.proxyserverlist24.top/feeds/lists/http",
        "proxy-list.org": "https://www.proxy-list.org/api/english/proxy?type=http",
        "spys.me": "http://spys.me/proxy.txt",
        "socks24.org": "https://www.socks24.org/ proxies",
        "proxymesh.com": "https://www.proxymesh.com/api/proxies",
    }

    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
        self.logger = get_logger("ProxyGrabber")

    def _parse_proxy_line(self, line: str, source: str = "") -> Optional[ProxyItem]:
        line = line.strip()
        if not line or ":" not in line:
            return None
        try:
            parts = line.split(":")
            if len(parts) >= 2:
                ip = parts[0].strip()
                port = int(parts[1].strip())
                proxy_type = ProxyType.HTTP
                if "socks4" in source:
                    proxy_type = ProxyType.SOCKS4
                elif "socks5" in source:
                    proxy_type = ProxyType.SOCKS5
                elif "https" in source:
                    proxy_type = ProxyType.HTTPS
                return ProxyItem(ip=ip, port=port, proxy_type=proxy_type, source=source)
        except (ValueError, IndexError):
            return None
        return None

    def grab_from_url(self, url: str, source_name: str = "") -> List[ProxyItem]:
        proxies = []
        try:
            response = self.client.get(url, timeout=15)
            if response.status_code == 200:
                for line in response.text.splitlines():
                    line = line.strip()
                    if line and ":" in line:
                        proxy = self._parse_proxy_line(line, source_name)
                        if proxy:
                            proxies.append(proxy)
        except Exception as e:
            self.logger.warning(f"Grab from {url} error: {e}")
        return proxies

    def grab_github_all(self, max_per_source: int = 50) -> List[ProxyItem]:
        all_proxies = []
        seen = set()

        for repo_name, sources in self.GITHUB_PROXY_SOURCES.items():
            for proxy_type, url in sources.items():
                proxies = self.grab_from_url(url, f"github:{repo_name}")
                for proxy in proxies[:max_per_source]:
                    key = f"{proxy.ip}:{proxy.port}"
                    if key not in seen:
                        seen.add(key)
                        all_proxies.append(proxy)
                time.sleep(0.5)

        return all_proxies

    def grab_public_all(self) -> List[ProxyItem]:
        all_proxies = []
        seen = set()

        for source_name, url in self.FREE_PROXY_SOURCES.items():
            if "proxyscrape" in source_name or "proxy-list.download" in source_name or "geonode" in source_name or "spys.me" in source_name:
                proxies = self.grab_from_url(url, source_name)
                for proxy in proxies[:100]:
                    key = f"{proxy.ip}:{proxy.port}"
                    if key not in seen:
                        seen.add(key)
                        all_proxies.append(proxy)
            time.sleep(0.5)

        return all_proxies

    def grab_all(self) -> List[ProxyItem]:
        github_proxies = self.grab_github_all()
        public_proxies = self.grab_public_all()

        seen = {f"{p.ip}:{p.port}" for p in github_proxies}
        for proxy in public_proxies:
            key = f"{proxy.ip}:{proxy.port}"
            if key not in seen:
                seen.add(key)
                github_proxies.append(proxy)

        return github_proxies

    def close(self):
        self.client.close()


class ProxyValidator:
    """
    代理验证器 - 支持并发验证代理可用性
    """
    TEST_URLS = [
        "https://httpbin.org/ip",
        "https://api.ipify.org?format=json",
        "https://ipinfo.io/json",
    ]

    def __init__(self, max_concurrent: int = 50):
        self.max_concurrent = max_concurrent
        self.logger = get_logger("ProxyValidator")

    async def _check_single_async(self, session: aiohttp.ClientSession, proxy: ProxyItem,
                                   timeout: int = 10) -> Tuple[ProxyItem, bool, float]:
        start_time = time.time()
        test_url = self.TEST_URLS[0]

        proxy_url = proxy.proxy_str
        try:
            async with session.get(test_url, proxy=proxy_url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                if response.status == 200:
                    latency = time.time() - start_time
                    proxy.latency = latency
                    proxy.status = ProxyStatus.WORKING
                    proxy.success_count += 1
                    proxy.last_checked = datetime.now()
                    proxy.last_success = datetime.now()
                    return proxy, True, latency
        except Exception:
            pass

        proxy.status = ProxyStatus.FAILED
        proxy.fail_count += 1
        proxy.last_checked = datetime.now()
        return proxy, False, 0.0

    async def _validate_batch_async(self, proxies: List[ProxyItem]) -> List[ProxyItem]:
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def _validate_with_semaphore(session: aiohttp.ClientSession, proxy: ProxyItem):
            async with semaphore:
                return await self._check_single_async(session, proxy)

        async with aiohttp.ClientSession() as session:
            tasks = [_validate_with_semaphore(session, proxy) for proxy in proxies]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        validated = []
        for result in results:
            if isinstance(result, tuple):
                validated.append(result[0])
        return validated

    def validate_sync(self, proxies: List[ProxyItem], max_workers: int = 20) -> List[ProxyItem]:
        import concurrent.futures

        def check_proxy(proxy: ProxyItem) -> Tuple[ProxyItem, bool, float]:
            start_time = time.time()
            test_url = self.TEST_URLS[0]
            proxy_url = proxy.proxy_str

            try:
                response = httpx.get(test_url, proxy=proxy_url, timeout=10)
                if response.status_code == 200:
                    latency = time.time() - start_time
                    proxy.latency = latency
                    proxy.status = ProxyStatus.WORKING
                    proxy.success_count += 1
                    proxy.last_checked = datetime.now()
                    proxy.last_success = datetime.now()
                    return proxy, True, latency
            except Exception:
                pass

            proxy.status = ProxyStatus.FAILED
            proxy.fail_count += 1
            proxy.last_checked = datetime.now()
            return proxy, False, 0.0

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(check_proxy, p): p for p in proxies}
            results = []
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result[0])

        return results

    def validate(self, proxies: List[ProxyItem], async_mode: bool = True) -> List[ProxyItem]:
        if async_mode:
            return asyncio.run(self._validate_batch_async(proxies))
        return self.validate_sync(proxies)


class ProxyManager:
    """
    统一代理管理器 - 整合采集、验证、存储、调用功能
    支持 SQLite 持久化存储代理
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_path: str = "results/proxies.db"):
        self.db_path = db_path
        self.logger = get_logger("ProxyManager")
        self._ensure_db()
        self.grabber = ProxyGrabberProvider()
        self.validator = ProxyValidator()
        self._proxy_cache: List[ProxyItem] = []
        self._last_grab: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=30)

    def _ensure_db(self):
        os.makedirs(os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else "results", exist_ok=True)
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proxies (
                ip TEXT NOT NULL,
                port INTEGER NOT NULL,
                proxy_type TEXT DEFAULT 'http',
                country TEXT DEFAULT '',
                latency REAL DEFAULT 0,
                anonymity TEXT DEFAULT '',
                status TEXT DEFAULT 'untried',
                success_count INTEGER DEFAULT 0,
                fail_count INTEGER DEFAULT 0,
                last_checked TEXT,
                last_success TEXT,
                source TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (ip, port)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS grab_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grab_time TEXT,
                total_count INTEGER,
                working_count INTEGER
            )
        """)
        conn.commit()
        conn.close()

    def save_proxy(self, proxy: ProxyItem):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO proxies
            (ip, port, proxy_type, country, latency, anonymity, status,
             success_count, fail_count, last_checked, last_success, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            proxy.ip, proxy.port, proxy.proxy_type.value, proxy.country,
            proxy.latency, proxy.anonymity, proxy.status.value,
            proxy.success_count, proxy.fail_count,
            proxy.last_checked.isoformat() if proxy.last_checked else None,
            proxy.last_success.isoformat() if proxy.last_success else None,
            proxy.source
        ))
        conn.commit()
        conn.close()

    def save_proxies(self, proxies: List[ProxyItem]):
        for proxy in proxies:
            self.save_proxy(proxy)

    def load_proxies(self, status: Optional[ProxyStatus] = None,
                     min_score: float = 0.0,
                     limit: int = 100,
                     proxy_type: Optional[ProxyType] = None) -> List[ProxyItem]:
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM proxies WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status.value)

        if min_score > 0:
            query += " AND (success_count * 1.0 / (success_count + fail_count + 1)) >= ?"
            params.append(min_score)

        if proxy_type:
            query += " AND proxy_type = ?"
            params.append(proxy_type.value)

        query += " ORDER BY (success_count * 1.0 / (success_count + fail_count + 1)) DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        proxies = []
        for row in rows:
            proxy = ProxyItem(
                ip=row[0], port=row[1],
                proxy_type=ProxyType(row[2]) if row[2] else ProxyType.HTTP,
                country=row[3] or "",
                latency=row[4] or 0,
                anonymity=row[5] or "",
                status=ProxyStatus(row[6]) if row[6] else ProxyStatus.UNTRIED,
                success_count=row[7] or 0,
                fail_count=row[8] or 0,
                last_checked=datetime.fromisoformat(row[9]) if row[9] else None,
                last_success=datetime.fromisoformat(row[10]) if row[10] else None,
                source=row[11] or ""
            )
            proxies.append(proxy)

        return proxies

    def grab_and_validate(self, save: bool = True) -> Tuple[int, int]:
        self.logger.info("Starting proxy grab and validate...")
        proxies = self.grabber.grab_all()
        self.logger.info(f"Grabbed {len(proxies)} proxies from all sources")

        validated = self.validator.validate(proxies)
        working = [p for p in validated if p.status == ProxyStatus.WORKING]
        self.logger.info(f"Working proxies: {len(working)}")

        if save:
            self.save_proxies(validated)

            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO grab_history (grab_time, total_count, working_count)
                VALUES (?, ?, ?)
            """, (datetime.now().isoformat(), len(proxies), len(working)))
            conn.commit()
            conn.close()

        self._proxy_cache = working
        self._last_grab = datetime.now()
        return len(proxies), len(working)

    def get_working_proxies(self, limit: int = 50) -> List[ProxyItem]:
        if not self._proxy_cache or self._last_grab is None or \
           datetime.now() - self._last_grab > self._cache_ttl:
            self._proxy_cache = self.load_proxies(status=ProxyStatus.WORKING, limit=limit)
            self._last_grab = datetime.now()
        return self._proxy_cache[:limit]

    def get_random_working(self, proxy_type: Optional[ProxyType] = None) -> Optional[ProxyItem]:
        working = self.get_working_proxies(limit=200)
        if proxy_type:
            working = [p for p in working if p.proxy_type == proxy_type]
        if working:
            import random
            return random.choice(working)
        return None

    def record_success(self, proxy: ProxyItem):
        proxy.success_count += 1
        proxy.last_success = datetime.now()
        proxy.status = ProxyStatus.WORKING
        self.save_proxy(proxy)

    def record_failure(self, proxy: ProxyItem):
        proxy.fail_count += 1
        if proxy.fail_count >= 3:
            proxy.status = ProxyStatus.FAILED
        self.save_proxy(proxy)

    def stats(self) -> dict:
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM proxies")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM proxies WHERE status = 'working'")
        working = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM proxies WHERE status = 'failed'")
        failed = cursor.fetchone()[0]

        cursor.execute("SELECT AVG(latency) FROM proxies WHERE latency > 0")
        avg_latency = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM grab_history ORDER BY grab_time DESC LIMIT 1")
        last_grab = cursor.fetchone()[0]

        conn.close()

        return {
            "total": total,
            "working": working,
            "failed": failed,
            "untried": total - working - failed,
            "avg_latency": round(avg_latency, 3),
            "last_grab": last_grab
        }


class ProxyGrabberTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.provider = None
        self.manager = None

    def validate(self) -> bool:
        return True

    def execute(self) -> TaskResult:
        try:
            self.provider = ProxyGrabberProvider()
            proxies = self.provider.grab_all()

            self.logger.info(f"ProxyGrabber: grabbed {len(proxies)} proxies")

            if proxies:
                sample_file = self.results_dir + "/proxies.txt"
                os.makedirs(self.results_dir, exist_ok=True)
                with open(sample_file, "w") as f:
                    for proxy in proxies[:100]:
                        f.write(f"{proxy.proxy_str}\n")

                self.save_account(
                    str(len(proxies)) + "_proxies",
                    "",
                    count=str(len(proxies)),
                    sample_file=sample_file
                )

            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.SUCCESS,
                message=f"ProxyGrabber: grabbed {len(proxies)} proxies",
                data={"proxy_count": len(proxies)}
            )

        except Exception as e:
            self.logger.error(f"ProxyGrabber error: {e}", e)
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
        finally:
            if self.provider:
                self.provider.close()


class ProxyManagerTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.manager = None

    def validate(self) -> bool:
        return True

    def execute(self) -> TaskResult:
        try:
            db_path = self.global_config.get("proxy_services", {}).get("db_path", "results/proxies.db")
            self.manager = ProxyManager(db_path=db_path)

            grab_count, working_count = self.manager.grab_and_validate()

            stats = self.manager.stats()

            self.logger.info(f"ProxyManager: grabbed {grab_count}, working {working_count}")
            self.logger.info(f"Stats: {stats}")

            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.SUCCESS,
                message=f"ProxyManager: grabbed {grab_count}, working {working_count}",
                data={
                    "grab_count": grab_count,
                    "working_count": working_count,
                    "stats": stats
                }
            )

        except Exception as e:
            self.logger.error(f"ProxyManager error: {e}", e)
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
