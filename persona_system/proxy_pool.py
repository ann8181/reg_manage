import uuid
import asyncio
import httpx
from datetime import datetime
from typing import List, Optional, Dict

class ProxyPoolManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        from .database import JSONDatabase
        self.db = JSONDatabase(db_path)
    
    def add_proxy(
        self,
        host: str,
        port: int,
        protocol: str = "http",
        username: Optional[str] = None,
        password: Optional[str] = None,
        country: str = "US",
        location: Optional[str] = None
    ) -> Dict:
        proxy = {
            "id": str(uuid.uuid4()),
            "proxy": {
                "host": host,
                "port": port,
                "protocol": protocol,
                "auth": {
                    "username": username,
                    "password": password
                } if username else None
            },
            "location": {
                "country": country,
                "city": location or "",
                "isp": ""
            },
            "quality": {
                "anonymity": "unknown",
                "speed_ms": 0,
                "uptime": 0,
                "last_checked": None
            },
            "status": "testing",
            "assigned_identity_id": None,
            "cost_per_gb": 0,
            "daily_limit_gb": 0,
            "added_at": datetime.now().isoformat(),
            "last_used_at": None,
            "usage_count": 0
        }
        return self.db.add(proxy)
    
    def add_proxy_from_string(self, proxy_str: str, country: str = "US") -> Optional[Dict]:
        parts = proxy_str.split("@")
        if len(parts) == 2:
            auth, host_port = parts
            username, password = auth.split(":")
            host, port = host_port.split(":")
            return self.add_proxy(host, int(port), "http", username, password, country)
        elif len(parts) == 1:
            host_port = parts[0]
            if ":" in host_port:
                host, port = host_port.split(":")
                return self.add_proxy(host, int(port), "http", country=country)
        return None
    
    async def check_proxy_quality_async(self, proxy_id: str) -> Optional[Dict]:
        proxy = self.db.get_by_id(proxy_id)
        if not proxy:
            return None
        
        proxy_info = proxy.get("proxy", {})
        host = proxy_info.get("host")
        port = proxy_info.get("port")
        protocol = proxy_info.get("protocol", "http")
        
        result = {
            "anonymity": "unknown",
            "speed_ms": 0,
            "uptime": 100,
            "last_checked": datetime.now().isoformat()
        }
        
        proxy_url = f"{protocol}://{host}:{port}"
        if proxy_info.get("auth"):
            auth = proxy_info.get("auth", {})
            proxy_url = f"{protocol}://{auth.get('username')}:{auth.get('password')}@{host}:{port}"
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                start = datetime.now()
                response = await client.get(
                    "https://httpbin.org/ip",
                    proxy=proxy_url
                )
                elapsed = (datetime.now() - start).total_seconds() * 1000
                
                if response.status_code == 200:
                    result["speed_ms"] = int(elapsed)
                    result["anonymity"] = await self._check_anonymity_async(client, proxy_url)
                    
                    ip_info = response.json().get("origin", "").split(",")
                    if len(ip_info) > 1:
                        result["anonymity"] = "elite"
        except Exception:
            result["uptime"] = 0
            result["anonymity"] = "failed"
        
        self.db.update(proxy_id, {"quality": result, "status": "active" if result["uptime"] > 0 else "dead"})
        return result
    
    async def _check_anonymity_async(self, client: httpx.AsyncClient, proxy_url: str) -> str:
        try:
            response = await client.get(
                "https://httpbin.org/headers",
                proxy=proxy_url
            )
            if response.status_code == 200:
                headers = response.json().get("headers", {})
                if "X-Forwarded-For" in headers or "X-Real-IP" in headers:
                    return "transparent"
                return "elite"
        except:
            pass
        return "unknown"
    
    def check_proxy_quality(self, proxy_id: str) -> Optional[Dict]:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.ensure_future(self.check_proxy_quality_async(proxy_id))
                return future.result()
            else:
                return loop.run_until_complete(self.check_proxy_quality_async(proxy_id))
        except:
            return None
    
    def get_best_proxy(self, country: Optional[str] = None, min_score: int = 60) -> Optional[Dict]:
        all_proxies = self.db.get_all()
        available = []
        
        for proxy in all_proxies:
            if proxy.get("status") not in ["active", "testing"]:
                continue
            if country and proxy.get("location", {}).get("country") != country:
                continue
            if proxy.get("assigned_identity_id"):
                continue
            
            score = self._calculate_proxy_score(proxy)
            if score >= min_score:
                available.append((proxy, score))
        
        if available:
            available.sort(key=lambda x: x[1], reverse=True)
            return available[0][0]
        return None
    
    def _calculate_proxy_score(self, proxy: Dict) -> int:
        score = 100
        quality = proxy.get("quality", {})
        
        anonymity_scores = {"elite": 0, "anonymous": 30, "transparent": 70, "unknown": 50}
        anonymity = quality.get("anonymity", "unknown")
        score -= anonymity_scores.get(anonymity, 50)
        
        speed = quality.get("speed_ms", 9999)
        if speed > 2000:
            score -= 50
        elif speed > 1000:
            score -= 30
        elif speed > 500:
            score -= 15
        elif speed > 200:
            score -= 5
        
        uptime = quality.get("uptime", 0)
        score -= (100 - uptime) * 0.3
        
        return max(0, min(100, score))
    
    def assign_proxy_to_identity(self, proxy_id: str, identity_id: str) -> bool:
        proxy = self.db.get_by_id(proxy_id)
        if proxy and not proxy.get("assigned_identity_id"):
            self.db.update(proxy_id, {
                "assigned_identity_id": identity_id,
                "last_used_at": datetime.now().isoformat(),
                "usage_count": proxy.get("usage_count", 0) + 1
            })
            return True
        return False
    
    def release_proxy(self, proxy_id: str):
        self.db.update(proxy_id, {
            "assigned_identity_id": None,
            "last_used_at": datetime.now().isoformat()
        })
    
    def mark_proxy_dead(self, proxy_id: str, reason: str = ""):
        self.db.update(proxy_id, {
            "status": "dead",
            "metadata": {"death_reason": reason, "died_at": datetime.now().isoformat()}
        })
    
    def mark_proxy_banned(self, proxy_id: str, service: str = ""):
        self.db.update(proxy_id, {
            "status": "banned",
            "metadata": {"banned_for_service": service, "banned_at": datetime.now().isoformat()}
        })
    
    def get_proxies_by_country(self, country: str) -> List[Dict]:
        all_proxies = self.db.get_all()
        return [p for p in all_proxies if p.get("location", {}).get("country") == country]
    
    def get_available_proxies(self, country: Optional[str] = None) -> List[Dict]:
        all_proxies = self.db.get_all()
        available = []
        for p in all_proxies:
            if p.get("status") == "active" and not p.get("assigned_identity_id"):
                if country is None or p.get("location", {}).get("country") == country:
                    available.append(p)
        return available
    
    def get_stats(self) -> Dict:
        all_proxies = self.db.get_all()
        by_status = {}
        by_country = {}
        
        for proxy in all_proxies:
            status = proxy.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1
            
            country = proxy.get("location", {}).get("country", "unknown")
            by_country[country] = by_country.get(country, 0) + 1
        
        return {
            "total": len(all_proxies),
            "by_status": by_status,
            "by_country": by_country,
            "available": len(self.get_available_proxies())
        }
    
    def delete_proxy(self, proxy_id: str) -> bool:
        return self.db.delete(proxy_id)
    
    async def batch_check_quality(self, proxy_ids: List[str]) -> Dict[str, Dict]:
        results = {}
        tasks = [self.check_proxy_quality_async(pid) for pid in proxy_ids]
        outcomes = await asyncio.gather(*tasks, return_exceptions=True)
        
        for pid, result in zip(proxy_ids, outcomes):
            if isinstance(result, Exception):
                results[pid] = {"error": str(result)}
            else:
                results[pid] = result
        return results
