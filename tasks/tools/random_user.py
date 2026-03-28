import httpx
import random
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum
from core.logger import get_task_logger


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"


@dataclass
class Person:
    gender: str
    name_title: str
    name_first: str
    name_last: str
    email: str
    phone: str
    cell: str
    location_street: str
    location_city: str
    location_state: str
    location_postcode: str
    location_country: str
    latitude: str
    longitude: str
    timezone_offset: str
    timezone_description: str
    dob_date: str
    dob_age: int
    registered_date: str
    registered_age: int
    id_name: str
    id_value: str
    picture_large: str
    picture_medium: str
    picture_thumbnail: str
    nat: str
    
    @property
    def full_name(self) -> str:
        return f"{self.name_title} {self.name_first} {self.name_last}"
    
    @property
    def full_address(self) -> str:
        return f"{self.location_street}, {self.location_city}, {self.location_state} {self.location_postcode}, {self.location_country}"


class RandomUserGenerator:
    def __init__(self):
        self.base_url = "https://randomuser.me/api"
        self.client = httpx.Client(timeout=30.0)
    
    def generate(self, gender: Gender = None, nat: str = None) -> Optional[Person]:
        params = {}
        if gender:
            params["gender"] = gender.value
        if nat:
            params["nat"] = nat
        
        try:
            response = self.client.get(self.base_url, params=params)
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if results:
                    return self._parse_person(results[0])
        except Exception as e:
            print(f"[RandomUser] Generate error: {e}")
        return None
    
    def generate_batch(self, count: int = 10, gender: Gender = None, nat: str = None) -> List[Person]:
        params = {"results": count}
        if gender:
            params["gender"] = gender.value
        if nat:
            params["nat"] = nat
        
        try:
            response = self.client.get(self.base_url, params=params)
            if response.status_code == 200:
                data = response.json()
                return [self._parse_person(r) for r in data.get("results", [])]
        except Exception as e:
            print(f"[RandomUser] Generate batch error: {e}")
        return []
    
    def _parse_person(self, data: dict) -> Person:
        name = data.get("name", {})
        location = data.get("location", {})
        login = data.get("login", {})
        dob = data.get("dob", {})
        registered = data.get("registered", {})
        id_info = data.get("id", {})
        picture = data.get("picture", {})
        
        return Person(
            gender=data.get("gender", ""),
            name_title=name.get("title", ""),
            name_first=name.get("first", ""),
            name_last=name.get("last", ""),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            cell=data.get("cell", ""),
            location_street=f"{location.get('street', {}).get('number', '')} {location.get('street', {}).get('name', '')}",
            location_city=location.get("city", ""),
            location_state=location.get("state", ""),
            location_postcode=str(location.get("postcode", "")),
            location_country=location.get("country", ""),
            latitude=location.get("coordinates", {}).get("latitude", ""),
            longitude=location.get("coordinates", {}).get("longitude", ""),
            timezone_offset=location.get("timezone", {}).get("offset", ""),
            timezone_description=location.get("timezone", {}).get("description", ""),
            dob_date=dob.get("date", ""),
            dob_age=dob.get("age", 0),
            registered_date=registered.get("date", ""),
            registered_age=registered.get("age", 0),
            id_name=id_info.get("name", ""),
            id_value=id_info.get("value", ""),
            picture_large=picture.get("large", ""),
            picture_medium=picture.get("medium", ""),
            picture_thumbnail=picture.get("thumbnail", ""),
            nat=data.get("nat", "")
        )
    
    def close(self):
        self.client.close()


def generate_person(gender: Gender = None, nat: str = None) -> Person:
    gen = RandomUserGenerator()
    person = gen.generate(gender, nat)
    gen.close()
    return person


def generate_persons(count: int = 10, gender: Gender = None, nat: str = None) -> List[Person]:
    gen = RandomUserGenerator()
    persons = gen.generate_batch(count, gender, nat)
    gen.close()
    return persons


class RandomUserTask:
    def __init__(self, config: dict, global_config: dict):
        self.config = config
        self.global_config = global_config
        self.logger = get_task_logger("random_user")
    
    def execute(self, gender: str = None, nat: str = None) -> dict:
        self.logger.info("Starting random user generation")
        try:
            gen = RandomUserGenerator()
            person = gen.generate(
                gender=Gender(gender) if gender else None,
                nat=nat
            )
            gen.close()
            
            if person:
                self.logger.info(f"Successfully generated user: {person.full_name}")
                return {
                    "status": "success",
                    "message": f"Generated person: {person.full_name}",
                    "data": {
                        "full_name": person.full_name,
                        "email": person.email,
                        "phone": person.phone,
                        "gender": person.gender,
                        "location": person.full_address,
                        "nat": person.nat
                    }
                }
            self.logger.error("Failed to generate person: no result returned")
            return {"status": "failed", "message": "Failed to generate person"}
        except Exception as e:
            self.logger.error(f"Random user generation failed: {e}")
            return {"status": "failed", "error": str(e)}


def RandomUserGenerateTask(config: dict, global_config: dict):
    return RandomUserTask(config, global_config)
