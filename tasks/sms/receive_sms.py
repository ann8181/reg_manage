import time
import httpx
import re
from typing import List, Dict, Optional
from enum import Enum


class Countries(Enum):
    USA = "united-states"
    UK = "united-kingdom"
    RUSSIA = "russia"
    UKRAINE = "ukraine"
    CHINA = "china"
    POLAND = "poland"
    FRANCE = "france"
    GERMANY = "germany"
    INDIA = "india"
    INDONESIA = "indonesia"


class PhoneNumber:
    def __init__(self, number: str, country: Countries, operator: str = ""):
        self.number = number
        self.country = country
        self.operator = operator


class Message:
    def __init__(self, sender: str, text: str, date: str = ""):
        self.sender = sender
        self.text = text
        self.date = date


class ReceiveSms:
    def __init__(self):
        self.base_url = "https://receive-sms-free.cc"
        self.client = httpx.Client(timeout=30.0)
        self.current_phone = None
        self.current_country = None
    
    def get_country(self, country: Countries) -> 'ReceiveSms':
        self.current_country = country
        return self
    
    def get_number(self) -> Optional[PhoneNumber]:
        if not self.current_country:
            return None
        
        try:
            response = self.client.get(
                f"{self.base_url}/api/getNumber",
                params={"country": self.current_country.value}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("number"):
                    self.current_phone = data["number"]
                    return PhoneNumber(
                        number=data["number"],
                        country=self.current_country,
                        operator=data.get("operator", "")
                    )
        except Exception as e:
            print(f"[ReceiveSms] Get number error: {e}")
        return None
    
    def get_last_messages(self) -> List[Message]:
        if not self.current_phone:
            return []
        
        try:
            response = self.client.get(
                f"{self.base_url}/api/getMessages",
                params={"phone": self.current_phone}
            )
            if response.status_code == 200:
                data = response.json()
                messages = []
                for msg in data.get("messages", []):
                    messages.append(Message(
                        sender=msg.get("from", ""),
                        text=msg.get("text", ""),
                        date=msg.get("date", "")
                    ))
                return messages
        except Exception as e:
            print(f"[ReceiveSms] Get messages error: {e}")
        return []
    
    def wait_for_message(self, max_wait: int = 120) -> Optional[Message]:
        start_time = time.time()
        while time.time() - start_time < max_wait:
            messages = self.get_last_messages()
            if messages:
                return messages[0]
            time.sleep(10)
        return None
    
    def extract_code(self, text: str = None) -> Optional[str]:
        target = text or (self.get_last_messages()[0].text if self.get_last_messages() else "")
        codes = re.findall(r'\b\d{6}\b', target)
        if codes:
            return codes[0]
        codes = re.findall(r'\b\d{4}\b', target)
        return codes[0] if codes else None
    
    def close(self):
        self.client.close()


class ReceiveSmsFreeTask:
    def __init__(self, config: dict, global_config: dict):
        self.config = config
        self.global_config = global_config
        self.provider = None
    
    def execute(self) -> dict:
        try:
            self.provider = ReceiveSms()
            phone = self.provider.get_number()
            
            if not phone:
                return {"status": "failed", "message": "Failed to get phone number"}
            
            return {
                "status": "success",
                "message": f"Phone number: {phone.number}",
                "data": {
                    "phone": phone.number,
                    "country": phone.country.value,
                    "operator": phone.operator
                }
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}
        finally:
            if self.provider:
                self.provider.close()


def ReceiveSmsTask(config: dict, global_config: dict):
    return ReceiveSmsFreeTask(config, global_config)
