import time
import httpx
import random
from typing import List, Dict, Optional
from core.base import TaskConfig, BaseTask, TaskResult, TaskStatus


class ProxyPoolProvider:
    def __init__(self, api_url: str = "http://localhost:8080"):
        self.api_url = api_url
        self.client = httpx.Client(timeout=30.0)
        self.proxies: List[Dict] = []
    
    def fetch_proxies(self, protocol: str = "http", anonymity: str = "all") -> List[Dict]:
        try:
            response = self.client.get(
                f"{self.api_url}/fetch",
                params={"protocol": protocol, "anonymity": anonymity}
            )
            if response.status_code == 200:
                self.proxies = response.json()
                return self.proxies
        except Exception as e:
            print(f"[ProxyPool] Fetch proxies error: {e}")
        return []
    
    def check_proxy(self, proxy: Dict) -> bool:
        try:
            proxy_url = f"{proxy.get('protocol', 'http')}://{proxy.get('host')}:{proxy.get('port')}"
            response = self.client.get(
                "https://httpbin.org/ip",
                proxies={"http": proxy_url, "https": proxy_url},
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"[ProxyPool] Check proxy error: {e}")
            return False
    
    def get_random_proxy(self, protocol: str = "http") -> Optional[Dict]:
        if not self.proxies:
            self.fetch_proxies(protocol)
        
        for _ in range(len(self.proxies)):
            proxy = random.choice(self.proxies)
            if self.check_proxy(proxy):
                return proxy
            self.proxies.remove(proxy)
        
        self.fetch_proxies(protocol)
        if self.proxies:
            return random.choice(self.proxies)
        return None
    
    def close(self):
        self.client.close()


class ProxyPoolTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.api_url = global_config.get("proxy_services", {}).get("pool", {}).get("api_url", "http://localhost:8080")
        self.provider = None
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        try:
            self.provider = ProxyPoolProvider(self.api_url)
            
            proxies = self.provider.fetch_proxies()
            self.logger.info(f"ProxyPool fetched {len(proxies)} proxies")
            
            if proxies:
                self.save_account(
                    f"{len(proxies)}_proxies",
                    "",
                    count=str(len(proxies)),
                    sample=f"{proxies[0].get('host')}:{proxies[0].get('port')}" if proxies else ""
                )
            
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.SUCCESS,
                message=f"ProxyPool fetched {len(proxies)} proxies",
                data={"proxy_count": len(proxies)}
            )
            
        except Exception as e:
            self.logger.error(f"ProxyPool error: {str(e)}", e)
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
        finally:
            if self.provider:
                self.provider.close()


class ProxyCheckerProvider:
    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
    
    def check_proxy(self, host: str, port: int, protocol: str = "http") -> Dict:
        proxy_url = f"{protocol}://{host}:{port}"
        result = {
            "host": host,
            "port": port,
            "protocol": protocol,
            "working": False,
            "latency": None
        }
        
        try:
            start = time.time()
            response = self.client.get(
                "https://httpbin.org/ip",
                proxies={"http": proxy_url, "https": proxy_url},
                timeout=10
            )
            result["latency"] = time.time() - start
            result["working"] = response.status_code == 200
        except Exception as e:
            print(f"[ProxyChecker] Check proxy error: {e}")
        
        return result
    
    def check_proxy_file(self, filepath: str) -> List[Dict]:
        results = []
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    parts = line.strip().split(':')
                    if len(parts) >= 2:
                        host, port = parts[0], int(parts[1])
                        result = self.check_proxy(host, port)
                        results.append(result)
                        if result["working"]:
                            self.save_account(
                                f"{host}:{port}",
                                "",
                                latency=str(result.get("latency", 0))
                            )
        except Exception as e:
            print(f"[ProxyChecker] Check file error: {e}")
        
        return results
    
    def close(self):
        self.client.close()


class ProxyCheckerTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.provider = None
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        try:
            self.provider = ProxyCheckerProvider()
            
            self.logger.info("ProxyChecker ready")
            
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.SUCCESS,
                message="ProxyChecker ready",
                data={"status": "ready"}
            )
            
        except Exception as e:
            self.logger.error(f"ProxyChecker error: {str(e)}", e)
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
        finally:
            if self.provider:
                self.provider.close()
