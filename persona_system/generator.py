import random
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from faker import Faker
from .fingerprint import FingerprintGenerator
from .quality import IdentityQualityScorer
import uuid

class IdentityGenerator:
    def __init__(self):
        self.fake = Faker('en_US')
        self.fingerprint_gen = FingerprintGenerator()
        self.quality_scorer = IdentityQualityScorer()
        self._usage_count = 0
    
    def generate(
        self,
        country: str = "US",
        gender: Optional[str] = None,
        age_range: tuple = (22, 45),
        quality_threshold: int = 0
    ) -> Dict:
        self._usage_count += 1
        
        gender = gender or random.choice(["Male", "Female"])
        
        name = self._generate_name(gender)
        location = self._generate_location()
        fingerprint = self.fingerprint_gen.generate()
        phone = self._generate_phone()
        
        age = random.randint(age_range[0], age_range[1])
        birthdate = self._calculate_birthdate(age)
        
        identity = {
            "id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "quality_score": 0,
            "status": "active",
            "profile": {
                "name": name,
                "demographics": {
                    "age": age,
                    "gender": gender,
                    "birthdate": birthdate
                },
                "location": location,
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
                "generation_count": self._usage_count,
                "country": country,
                "used_count": 0,
                "last_used_at": None
            }
        }
        
        identity["quality_score"] = self.quality_scorer.calculate_score(identity)
        
        return identity
    
    async def generate_with_external_api(
        self,
        country: str = "US",
        gender: Optional[str] = None,
        age_range: tuple = (22, 45)
    ) -> Optional[Dict]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"https://guowaidizhi.com/us/")
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_external_data(data, gender, age_range)
        except Exception:
            pass
        return self.generate(country, gender, age_range)
    
    def _parse_external_data(self, data: Dict, gender: Optional[str], age_range: tuple) -> Dict:
        gender = gender or data.get("gender", random.choice(["Male", "Female"]))
        age = random.randint(age_range[0], age_range[1])
        
        name = {
            "first": data.get("first_name", self.fake.first_name_male() if gender == "Male" else self.fake.first_name_female()),
            "last": data.get("last_name", self.fake.last_name()),
            "full": data.get("name", "")
        }
        if not name["full"]:
            name["full"] = f"{name['first']} {name['last']}"
        
        location = data.get("location", {})
        if not location:
            location = self._generate_location()
        else:
            location = {
                "country": location.get("country", "US"),
                "country_name": location.get("country_name", "United States"),
                "state": location.get("state", self.fake.state_abbr()),
                "city": location.get("city", self.fake.city()),
                "zipcode": location.get("zipcode", self.fake.zipcode()),
                "latitude": float(location.get("latitude", self.fake.latitude())),
                "longitude": float(location.get("longitude", self.fake.longitude())),
                "timezone": location.get("timezone", self.fake.timezone())
            }
        
        identity = {
            "id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "quality_score": 0,
            "status": "active",
            "profile": {
                "name": name,
                "demographics": {
                    "age": age,
                    "gender": gender,
                    "birthdate": self._calculate_birthdate(age)
                },
                "location": location,
                "browser_fingerprint": self.fingerprint_gen.generate(),
                "network": {"ip": "", "proxy": None},
                "phone": self._generate_phone(location.get("state", "CA"))
            },
            "metadata": {
                "source": "local_generator",
                "generation_method": "random",
                "generation_count": self._usage_count,
                "used_count": 0,
                "last_used_at": None
            }
        }
        
        identity["quality_score"] = self.quality_scorer.calculate_score(identity)
        return identity
    
    def _generate_name(self, gender: str) -> Dict:
        if gender == "Male":
            first = self.fake.first_name_male()
        elif gender == "Female":
            first = self.fake.first_name_female()
        else:
            first = self.fake.first_name()
        
        last = self.fake.last_name()
        return {
            "first": first,
            "last": last,
            "full": f"{first} {last}"
        }
    
    def _generate_location(self) -> Dict:
        return {
            "country": "US",
            "country_name": "United States",
            "state": self.fake.state_abbr(),
            "city": self.fake.city(),
            "zipcode": self.fake.zipcode(),
            "latitude": float(self.fake.latitude()),
            "longitude": float(self.fake.longitude()),
            "timezone": self.fake.timezone()
        }
    
    def _generate_phone(self, state: str = "CA") -> Dict:
        area_codes = {
            "CA": ["213", "310", "415", "510", "619", "858", "909"],
            "NY": ["212", "315", "516", "518", "607", "646", "718", "845", "914"],
            "TX": ["210", "214", "281", "469", "512", "713", "817", "903", "972"],
            "FL": ["305", "321", "352", "386", "407", "561", "727", "786", "850", "954"],
            "IL": ["217", "312", "618", "630", "708", "773", "779", "815", "847"],
            "PA": ["215", "267", "412", "484", "570", "610", "717", "724", "814"],
            "OH": ["216", "234", "330", "419", "440", "513", "567", "614", "740", "937"],
            "GA": ["229", "404", "470", "478", "678", "706", "770", "912"],
            "WA": ["206", "253", "360", "425", "509"],
            "AZ": ["480", "520", "602", "623", "928"],
            "MA": ["413", "508", "617", "774", "781", "978"],
            "CO": ["303", "719", "720", "970"],
            "OTHER": ["201", "202", "203", "205", "207", "208", "209", "301", "302", "304"]
        }
        
        codes = area_codes.get(state, area_codes["OTHER"])
        area_code = random.choice(codes)
        number = ''.join([str(random.randint(0, 9)) for _ in range(7)])
        
        return {
            "area_code": area_code,
            "number": number,
            "formatted": f"+1 ({area_code}) {number[:3]}-{number[3:]}"
        }
    
    def _calculate_birthdate(self, age: int) -> str:
        today = datetime.now()
        birth_year = today.year - age
        max_day_of_year = 365
        random_day = random.randint(1, max_day_of_year)
        birthdate = datetime(birth_year, 1, 1) + timedelta(days=random_day - 1)
        return birthdate.strftime("%Y-%m-%d")
    
    def generate_batch(self, count: int, **kwargs) -> List[Dict]:
        return [self.generate(**kwargs) for _ in range(count)]
    
    def mark_as_used(self, identity: Dict):
        identity["metadata"]["used_count"] = identity["metadata"].get("used_count", 0) + 1
        identity["metadata"]["last_used_at"] = datetime.now().isoformat()
        
        used_threshold = 10
        if identity["metadata"]["used_count"] >= used_threshold:
            identity["status"] = "used"
    
    def retire_identity(self, identity: Dict, reason: str = ""):
        identity["status"] = "retired"
        identity["metadata"]["retire_reason"] = reason
        identity["metadata"]["retired_at"] = datetime.now().isoformat()
