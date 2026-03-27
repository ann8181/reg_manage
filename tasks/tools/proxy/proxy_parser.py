import httpx
import re
from typing import List, Optional, Dict
from dataclasses import dataclass
from enum import Enum


class ProxyType(Enum):
    HTTP = "HTTP"
    HTTPS = "HTTPS"
    SOCKS4 = "SOCKS4"
    SOCKS5 = "SOCKS5"


class Countries(Enum):
    USA = "US"
    UK = "GB"
    CA = "CA"
    DE = "DE"
    FR = "FR"
    RU = "RU"
    CN = "CN"
    JP = "JP"
    KR = "KR"
    IN = "IN"
    AU = "AU"
    BR = "BR"
    NL = "NL"
    IT = "IT"
    ES = "ES"
    PL = "PL"
    UA = "UA"
    CY = "CY"


@dataclass
class Proxy:
    ip: str
    port: int
    proxy_type: ProxyType
    country: str = ""
    latency: float = 0.0
    anonymity: str = ""
    
    def strfproxy(self) -> str:
        if self.proxy_type in [ProxyType.SOCKS4, ProxyType.SOCKS5]:
            return f"{self.proxy_type.value.lower()}://{self.ip}:{self.port}"
        protocol = "https" if self.proxy_type == ProxyType.HTTPS else "http"
        return f"{protocol}://{self.ip}:{self.port}"


class Proxies:
    def __init__(self):
        self.proxies: List[Proxy] = []
        self.client = httpx.Client(timeout=30.0)
    
    def parse_proxies(self) -> int:
        sources = [
            self._parse_proxy_list_download,
            self._parse_ssl_proxies,
            self._parse_socks_proxy,
            self._parse_free_proxy_list,
            self._parse_proxy_scrape,
            self._parse_geonode,
        ]
        
        for source in sources:
            try:
                source()
            except Exception as e:
                print(f"[Proxies] Parse error from {source.__name__}: {e}")
        
        return len(self.proxies)
    
    def _parse_proxy_list_download(self):
        url = "https://www.proxy-list.download/api/v1/get?type=http"
        response = self.client.get(url)
        if response.status_code == 200:
            for line in response.text.strip().split("\n"):
                if ":" in line:
                    parts = line.strip().split(":")
                    if len(parts) == 2:
                        self.proxies.append(Proxy(
                            ip=parts[0],
                            port=int(parts[1]),
                            proxy_type=ProxyType.HTTP
                        ))
    
    def _parse_ssl_proxies(self):
        url = "https://www.sslproxies.org/"
        response = self.client.get(url)
        if response.status_code == 200:
            table = re.findall(r'<td>(\d+\.\d+\.\d+\.\d+)</td><td>(\d+)</td>', response.text)
            for ip, port in table:
                self.proxies.append(Proxy(
                    ip=ip,
                    port=int(port),
                    proxy_type=ProxyType.HTTPS
                ))
    
    def _parse_socks_proxy(self):
        url = "https://www.socks-proxy.net/"
        response = self.client.get(url)
        if response.status_code == 200:
            table = re.findall(r'<td>(\d+\.\d+\.\d+\.\d+)</td><td>(\d+)</td>', response.text)
            for ip, port in table[:10]:
                self.proxies.append(Proxy(
                    ip=ip,
                    port=int(port),
                    proxy_type=ProxyType.SOCKS4
                ))
    
    def _parse_free_proxy_list(self):
        url = "https://free-proxy-list.net/"
        response = self.client.get(url)
        if response.status_code == 200:
            table = re.findall(r'<td>(\d+\.\d+\.\d+\.\d+)</td><td>(\d+)</td><td>([\w\s]+)</td>', response.text)
            for ip, port, country in table[:20]:
                self.proxies.append(Proxy(
                    ip=ip,
                    port=int(port),
                    proxy_type=ProxyType.HTTP,
                    country=country.strip()
                ))
    
    def _parse_proxy_scrape(self):
        url = "https://api.proxyscrape.com/v2/"
        params = {"request": "displayproxies", "protocol": "http", "timeout": "10000", "country": "all"}
        response = self.client.get(url, params=params)
        if response.status_code == 200:
            for line in response.text.strip().split("\n"):
                if ":" in line:
                    parts = line.strip().split(":")
                    if len(parts) == 2:
                        self.proxies.append(Proxy(
                            ip=parts[0],
                            port=int(parts[1]),
                            proxy_type=ProxyType.HTTP
                        ))
    
    def _parse_geonode(self):
        url = "https://proxylist.geonode.com/api/proxy-list?limit=50&page=1&sort_by=speed&sort_type=asc"
        response = self.client.get(url)
        if response.status_code == 200:
            data = response.json()
            for item in data.get("data", []):
                self.proxies.append(Proxy(
                    ip=item.get("ip", ""),
                    port=item.get("port", 0),
                    proxy_type=ProxyType.HTTP,
                    country=item.get("country", "")
                ))
    
    def pop(self) -> Optional[Proxy]:
        if self.proxies:
            return self.proxies.pop(0)
        return None
    
    def get_random(self) -> Optional[Proxy]:
        import random
        if self.proxies:
            return random.choice(self.proxies)
        return None
    
    def filter_by_country(self, countries: List[str]) -> List[Proxy]:
        return [p for p in self.proxies if p.country in countries]
    
    def filter_by_type(self, proxy_type: ProxyType) -> List[Proxy]:
        return [p for p in self.proxies if p.proxy_type == proxy_type]
    
    def __len__(self) -> int:
        return len(self.proxies)
    
    def __repr__(self) -> str:
        return f"Proxies(proxies_count={len(self.proxies)})"
    
    def close(self):
        self.client.close()


class ProxyParserTask:
    def __init__(self, config: dict, global_config: dict):
        self.config = config
        self.global_config = global_config
    
    def execute(self) -> dict:
        try:
            proxies = Proxies()
            count = proxies.parse_proxies()
            proxy_list = [p.strfproxy() for p in proxies.proxies[:100]]
            proxies.close()
            
            return {
                "status": "success",
                "message": f"Parsed {count} proxies",
                "data": {
                    "count": count,
                    "proxies": proxy_list
                }
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}


def ProxyGrabberTask(config: dict, global_config: dict):
    return ProxyParserTask(config, global_config)
