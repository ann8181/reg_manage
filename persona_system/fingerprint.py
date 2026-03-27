import random
import hashlib
from typing import Dict, List

class FingerprintGenerator:
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    ]
    
    SCREEN_RESOLUTIONS = [
        "1920x1080", "2560x1440", "1366x768", 
        "1440x900", "1536x864", "1680x1050", "1600x900"
    ]
    
    TIMEZONES = [
        "America/New_York", "America/Los_Angeles", 
        "America/Chicago", "America/Denver", "America/Phoenix"
    ]
    
    LANGUAGES = ["en-US", "en-GB", "en-CA", "en-AU"]
    
    PLATFORMS = ["Win32", "MacIntel", "Linux x86_64"]
    
    WEBGL_VENDORS = [
        "Google Inc. (NVIDIA)",
        "Google Inc. (Intel)",
        "Google Inc. (AMD)",
        "Intel Inc.",
        "NVIDIA Corporation"
    ]
    
    WEBGL_RENDERERS = [
        "ANGLE (NVIDIA GeForce GTX 1060 Direct3D11 vs_5_0 ps_5_0)",
        "ANGLE (Intel Iris OpenGL Engine)",
        "ANGLE (AMD Radeon Pro 5500M Direct3D11)",
        "Intel Iris OpenGL Engine",
        "NVIDIA GeForce GTX 1060/PCIe/SSE2"
    ]
    
    def generate(self) -> Dict:
        return {
            "user_agent": random.choice(self.USER_AGENTS),
            "screen_resolution": random.choice(self.SCREEN_RESOLUTIONS),
            "timezone": random.choice(self.TIMEZONES),
            "language": random.choice(self.LANGUAGES),
            "platform": random.choice(self.PLATFORMS),
            "hardware_concurrency": random.choice([4, 8, 16]),
            "device_memory": random.choice([4, 8, 16]),
            "webgl_vendor": random.choice(self.WEBGL_VENDORS),
            "webgl_renderer": random.choice(self.WEBGL_RENDERERS),
            "canvas_hash": self._generate_canvas_hash(),
            "audio_hash": self._generate_audio_hash(),
            "webgl_params": self._generate_webgl_params()
        }
    
    def _generate_canvas_hash(self) -> str:
        patterns = [
            "floodfill3d",
            "beziercureves", 
            "arcfunctions",
            "radialgradient",
            "moveto-lineto"
        ]
        pattern = random.choice(patterns)
        seed = random.randint(1000000, 9999999)
        data = f"{pattern}-{seed}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def _generate_audio_hash(self) -> str:
        data = f"audio-{random.randint(1000000, 9999999)}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]
    
    def _generate_webgl_params(self) -> Dict:
        return {
            "max_texture_size": random.choice([4096, 8192, 16384]),
            "max_viewport_dims": random.choice(["[4096, 4096]", "[8192, 8192]"]),
            "vertex_shader": f"highp float; attribute vec2 pos; void main() {{ gl_Position = vec4(pos, 0.0, 1.0); }}",
            "fragment_shader": f"precision mediump float; void main() {{ gl_FragColor = vec4({random.random()}, {random.random()}, {random.random()}, 1.0); }}"
        }
    
    def generate_unique(self, existing: List[Dict]) -> Dict:
        for _ in range(100):
            fp = self.generate()
            is_unique = True
            for exist in existing:
                if (fp["canvas_hash"] == exist.get("browser_fingerprint", {}).get("canvas_hash")
                    or fp["audio_hash"] == exist.get("browser_fingerprint", {}).get("audio_hash")):
                    is_unique = False
                    break
            if is_unique:
                return fp
        return self.generate()
