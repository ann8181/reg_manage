import re
from typing import Dict, List

class IdentityQualityScorer:
    def __init__(self):
        self.weights = {
            "name": 25,
            "location": 25,
            "fingerprint": 30,
            "demographics": 20
        }
    
    def calculate_score(self, identity: Dict) -> int:
        score = 100
        profile = identity.get("profile", {})
        
        score -= self._check_name_quality(profile.get("name", {}))
        score -= self._check_location_quality(profile.get("location", {}))
        score -= self._check_fingerprint_quality(profile.get("browser_fingerprint", {}))
        score -= self._check_demographics_quality(profile.get("demographics", {}))
        
        return max(0, min(100, score))
    
    def _check_name_quality(self, name: Dict) -> int:
        penalty = 0
        first = name.get("first", "")
        last = name.get("last", "")
        
        if len(first) < 2 or len(last) < 2:
            penalty += 20
        
        if re.search(r'[0-9]', first) or re.search(r'[0-9]', last):
            penalty += 30
        
        common_fake = ["Test", "Fake", "Demo", "User", "Admin", "Temp"]
        if first in common_fake or last in common_fake:
            penalty += 25
        
        if first.lower() == last.lower():
            penalty += 30
        
        unusual_patterns = ["xxx", "aaa", "qqq", "111", "aaa"]
        if any(p in first.lower() for p in unusual_patterns):
            penalty += 20
        
        return penalty
    
    def _check_location_quality(self, location: Dict) -> int:
        penalty = 0
        
        zipcode = location.get("zipcode", "")
        if not zipcode or len(zipcode) != 5:
            penalty += 15
        elif not zipcode.isdigit():
            penalty += 10
        
        state = location.get("state", "")
        if not state or len(state) != 2:
            penalty += 10
        
        city = location.get("city", "")
        if not city or len(city) < 2:
            penalty += 10
        
        if location.get("latitude") and location.get("longitude"):
            lat = location.get("latitude", 0)
            lon = location.get("longitude", 0)
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                penalty += 10
        
        return penalty
    
    def _check_fingerprint_quality(self, fingerprint: Dict) -> int:
        penalty = 0
        
        if not fingerprint.get("user_agent"):
            penalty += 20
        elif len(fingerprint.get("user_agent", "")) < 50:
            penalty += 10
        
        if not fingerprint.get("canvas_hash"):
            penalty += 15
        
        if not fingerprint.get("audio_hash"):
            penalty += 10
        
        hw = fingerprint.get("hardware_concurrency", 0)
        if hw < 2 or hw > 64:
            penalty += 10
        
        mem = fingerprint.get("device_memory", 0)
        if mem < 1 or mem > 128:
            penalty += 5
        
        if not fingerprint.get("webgl_vendor") or not fingerprint.get("webgl_renderer"):
            penalty += 5
        
        return penalty
    
    def _check_demographics_quality(self, demographics: Dict) -> int:
        penalty = 0
        
        age = demographics.get("age", 0)
        if age < 18 or age > 70:
            penalty += 15
        elif age < 21 or age > 60:
            penalty += 5
        
        gender = demographics.get("gender", "")
        if gender not in ["Male", "Female"]:
            penalty += 10
        
        birthdate = demographics.get("birthdate", "")
        if birthdate:
            try:
                year = int(birthdate.split("-")[0])
                expected_age = 2026 - year
                if abs(expected_age - age) > 1:
                    penalty += 10
            except:
                penalty += 5
        
        return penalty
    
    def validate_for_service(self, identity: Dict, service: str) -> Dict[str, bool]:
        profile = identity.get("profile", {})
        demographics = profile.get("demographics", {})
        
        return {
            "has_name": bool(profile.get("name", {}).get("full")),
            "has_reasonable_age": 18 <= demographics.get("age", 0) <= 65,
            "has_valid_location": bool(profile.get("location", {}).get("city")),
            "has_fingerprint": bool(profile.get("browser_fingerprint", {}).get("user_agent")),
            "has_unique_fingerprint": self._is_fingerprint_unique(identity),
            "quality_above_threshold": identity.get("quality_score", 0) >= 60
        }
    
    def _is_fingerprint_unique(self, identity: Dict) -> bool:
        fp = identity.get("profile", {}).get("browser_fingerprint", {})
        return bool(fp.get("canvas_hash") and fp.get("audio_hash"))
    
    def get_quality_grade(self, score: int) -> str:
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"
    
    def get_quality_description(self, score: int) -> str:
        if score >= 90:
            return "Excellent - 优质身份，可用于高价值账号注册"
        elif score >= 80:
            return "Good - 良好身份，适用于大多数场景"
        elif score >= 70:
            return "Fair - 一般身份，建议用于低风险服务"
        elif score >= 60:
            return "Poor - 较差身份，仅用于批量注册"
        else:
            return "Very Poor - 建议重新生成"


class ProxyQualityChecker:
    def __init__(self):
        self.anonymity_levels = {
            "elite": 100,
            "anonymous": 70,
            "transparent": 30
        }
    
    def calculate_proxy_score(self, proxy: Dict) -> int:
        score = 100
        quality = proxy.get("quality", {})
        
        anonymity = quality.get("anonymity", "transparent")
        score -= (100 - self.anonymity_levels.get(anonymity, 0)) * 0.3
        
        speed = quality.get("speed_ms", 9999)
        if speed < 100:
            score -= 5
        elif speed < 500:
            score -= 15
        elif speed < 1000:
            score -= 25
        else:
            score -= 40
        
        uptime = quality.get("uptime", 0)
        score -= (100 - uptime) * 0.2
        
        return max(0, min(100, int(score)))
    
    def is_proxy_suitable(self, proxy: Dict, min_score: int = 60) -> bool:
        return self.calculate_proxy_score(proxy) >= min_score
