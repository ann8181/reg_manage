import os
import time
import httpx
from typing import List, Dict
from core.base import TaskConfig, BaseTask, TaskResult, TaskStatus


class ProxyGrabberProvider:
    FREE_PROXY_SOURCES = [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/mufeedVh/proxy-list/main/PROXY/http.txt",
    ]
    
    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
        self.proxies: List[str] = []
    
    def grab_from_source(self, url: str) -> List[str]:
        proxies = []
        try:
            response = self.client.get(url, timeout=10)
            if response.status_code == 200:
                for line in response.text.splitlines():
                    line = line.strip()
                    if line and ":" in line:
                        proxies.append(line)
        except Exception as e:
            print("[ProxyGrabber] Grab from " + url + " error: " + str(e))
        return proxies
    
    def grab_all(self) -> List[str]:
        all_proxies = []
        for source in self.FREE_PROXY_SOURCES:
            proxies = self.grab_from_source(source)
            all_proxies.extend(proxies)
            time.sleep(1)
        return list(set(all_proxies))
    
    def close(self):
        self.client.close()


class ProxyGrabberTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.provider = None
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        try:
            self.provider = ProxyGrabberProvider()
            proxies = self.provider.grab_all()
            
            self.logger.info("ProxyGrabber: grabbed " + str(len(proxies)) + " proxies")
            
            if proxies:
                sample_file = self.results_dir + "/proxies.txt"
                os.makedirs(self.results_dir, exist_ok=True)
                with open(sample_file, "w") as f:
                    f.write("\n".join(proxies[:100]))
                
                self.save_account(
                    str(len(proxies)) + "_proxies",
                    "",
                    count=str(len(proxies)),
                    sample_file=sample_file
                )
            
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.SUCCESS,
                message="ProxyGrabber: grabbed " + str(len(proxies)) + " proxies",
                data={"proxy_count": len(proxies)}
            )
            
        except Exception as e:
            self.logger.error("ProxyGrabber error: " + str(e), e)
            return TaskResult(
                task_id=self.config.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
        finally:
            if self.provider:
                self.provider.close()
