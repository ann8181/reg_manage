from typing import Optional, Dict, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field

class BrowserFingerprint(BaseModel):
    user_agent: str = ""
    screen_resolution: str = "1920x1080"
    timezone: str = "America/New_York"
    language: str = "en-US"
    platform: str = "Win32"
    hardware_concurrency: int = 8
    device_memory: int = 8
    webgl_vendor: str = ""
    webgl_renderer: str = ""
    canvas_hash: str = ""
    audio_hash: str = ""
    webgl_params: Dict = {}

class ProxyInfo(BaseModel):
    host: str
    port: int
    protocol: Literal["http", "socks5"] = "http"
    auth: Optional[Dict] = None

class NameInfo(BaseModel):
    first: str
    last: str
    full: str

class LocationInfo(BaseModel):
    country: str = "US"
    country_name: str = "United States"
    state: str = ""
    city: str = ""
    zipcode: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    timezone: str = ""

class PhoneInfo(BaseModel):
    area_code: str = ""
    number: str = ""
    formatted: str = ""

class NetworkInfo(BaseModel):
    ip: str = ""
    proxy: Optional[ProxyInfo] = None

class IdentityProfile(BaseModel):
    name: NameInfo
    demographics: Dict = {}
    location: LocationInfo = LocationInfo()
    browser_fingerprint: BrowserFingerprint = BrowserFingerprint()
    network: NetworkInfo = NetworkInfo()
    phone: PhoneInfo = PhoneInfo()

class IdentityMetadata(BaseModel):
    source: str = "local_generator"
    generation_method: str = "random"
    used_count: int = 0
    last_used_at: Optional[str] = None

class Identity(BaseModel):
    id: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.now)
    quality_score: int = 0
    status: Literal["active", "used", "retired"] = "active"
    profile: IdentityProfile = IdentityProfile()
    metadata: IdentityMetadata = IdentityMetadata()

class ServiceInfo(BaseModel):
    name: str
    display_name: str = ""
    signup_url: str = ""
    category: str = "other"

class Credentials(BaseModel):
    email: str = ""
    password: str = ""
    username: str = ""
    phone: str = ""
    access_token: Optional[str] = None
    recovery_info: Dict = {}

class AccountMetadata(BaseModel):
    registration_proxy: Optional[str] = None
    browser_fingerprint_id: Optional[str] = None
    verification_method: str = "email"
    success: bool = True

class Account(BaseModel):
    id: str = Field(default="")
    identity_id: str = ""
    service: ServiceInfo = ServiceInfo(name="unknown")
    credentials: Credentials = Credentials()
    status: Literal["active", "locked", "disabled", "suspended", "deleted"] = "active"
    registered_at: datetime = Field(default_factory=datetime.now)
    last_used_at: Optional[datetime] = None
    access_token: Optional[str] = None
    recovery_info: Dict = {}
    metadata: AccountMetadata = AccountMetadata()
    notes: str = ""

class ProxyQuality(BaseModel):
    anonymity: Literal["elite", "anonymous", "transparent", "unknown"] = "unknown"
    speed_ms: int = 0
    uptime: float = 0
    last_checked: Optional[str] = None

class ProxyLocation(BaseModel):
    country: str = "US"
    city: str = ""
    isp: str = ""

class Proxy(BaseModel):
    id: str = Field(default="")
    proxy: ProxyInfo = ProxyInfo(host="", port=0)
    location: ProxyLocation = ProxyLocation()
    quality: ProxyQuality = ProxyQuality()
    status: Literal["active", "testing", "dead", "banned"] = "testing"
    assigned_identity_id: Optional[str] = None
    cost_per_gb: float = 0
    daily_limit_gb: float = 0
    added_at: str = ""
    last_used_at: Optional[str] = None
    usage_count: int = 0

class TaskStep(BaseModel):
    name: str
    status: Literal["pending", "running", "success", "failed"] = "pending"
    details: Dict = {}
    timestamp: str = ""

class TaskRecord(BaseModel):
    id: str = Field(default="")
    task_type: str = ""
    service: str = ""
    identity_id: Optional[str] = None
    proxy_id: Optional[str] = None
    account_id: Optional[str] = None
    status: Literal["pending", "running", "success", "failed"] = "pending"
    started_at: str = ""
    completed_at: Optional[str] = None
    duration_seconds: float = 0
    steps: List[TaskStep] = []
    error: Optional[Dict] = None
    result: Dict = {}

def create_identity_dict(
    first_name: str,
    last_name: str,
    age: int,
    gender: str,
    city: str,
    state: str,
    zipcode: str,
    fingerprint: Dict,
    phone: Dict
) -> Dict:
    return {
        "id": "",
        "created_at": datetime.now().isoformat(),
        "quality_score": 0,
        "status": "active",
        "profile": {
            "name": {
                "first": first_name,
                "last": last_name,
                "full": f"{first_name} {last_name}"
            },
            "demographics": {
                "age": age,
                "gender": gender,
                "birthdate": ""
            },
            "location": {
                "country": "US",
                "country_name": "United States",
                "state": state,
                "city": city,
                "zipcode": zipcode,
                "latitude": 0.0,
                "longitude": 0.0,
                "timezone": ""
            },
            "browser_fingerprint": fingerprint,
            "network": {
                "ip": "",
                "proxy": None
            },
            "phone": phone
        },
        "metadata": {
            "source": "local_generator",
            "generation_method": "random",
            "used_count": 0,
            "last_used_at": None
        }
    }
