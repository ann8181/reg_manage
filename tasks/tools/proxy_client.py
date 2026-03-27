from typing import Optional, List, Dict
from tasks.tools.proxy import ProxyManager, ProxyType, ProxyItem, ProxyStatus


class ProxyClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_path: str = "results/proxies.db"):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._manager = ProxyManager(db_path=db_path)

    def get_random(self, proxy_type: Optional[str] = None) -> Optional[str]:
        ptype = ProxyType(proxy_type) if proxy_type else None
        proxy = self._manager.get_random_working(proxy_type=ptype)
        return proxy.proxy_str if proxy else None

    def get_for_httpx(self, proxy_type: Optional[str] = None) -> Optional[Dict[str, str]]:
        proxy_str = self.get_random(proxy_type)
        if proxy_str:
            return {"http://": proxy_str, "https://": proxy_str}
        return None

    def record_success(self, proxy_str: str):
        try:
            parts = proxy_str.split("://")
            if len(parts) == 2:
                protocol, addr = parts
                ip_port = addr.split(":")
                if len(ip_port) == 2:
                    ip, port = ip_port
                    proxies = self._manager.load_proxies(limit=1000)
                    for p in proxies:
                        if p.ip == ip and p.port == int(port):
                            self._manager.record_success(p)
                            break
        except Exception:
            pass

    def record_failure(self, proxy_str: str):
        try:
            parts = proxy_str.split("://")
            if len(parts) == 2:
                protocol, addr = parts
                ip_port = addr.split(":")
                if len(ip_port) == 2:
                    ip, port = ip_port
                    proxies = self._manager.load_proxies(limit=1000)
                    for p in proxies:
                        if p.ip == ip and p.port == int(port):
                            self._manager.record_failure(p)
                            break
        except Exception:
            pass

    def grab_and_validate(self) -> Dict:
        grab_count, working_count = self._manager.grab_and_validate()
        return {
            "grabbed": grab_count,
            "working": working_count,
            "stats": self._manager.stats()
        }

    def get_stats(self) -> Dict:
        return self._manager.stats()

    def list_working(self, limit: int = 50) -> List[str]:
        proxies = self._manager.get_working_proxies(limit=limit)
        return [p.proxy_str for p in proxies]


def get_proxy_client(db_path: str = "results/proxies.db") -> ProxyClient:
    return ProxyClient(db_path=db_path)


def use_proxy(proxy_type: Optional[str] = None, db_path: str = "results/proxies.db") -> Optional[Dict[str, str]]:
    client = get_proxy_client(db_path)
    return client.get_for_httpx(proxy_type)


def report_proxy_success(proxy_str: str, db_path: str = "results/proxies.db"):
    client = get_proxy_client(db_path)
    client.record_success(proxy_str)


def report_proxy_failure(proxy_str: str, db_path: str = "results/proxies.db"):
    client = get_proxy_client(db_path)
    client.record_failure(proxy_str)
