import time
import email as email_lib
import imaplib
from typing import Dict, List, Optional
from core.base import TaskConfig, BaseTask, TaskResult, TaskStatus


class GmailClient(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
        self.imap_server = "imap.gmail.com"
        self.imap_port = 993
    
    def validate(self) -> bool:
        return True
    
    def connect(self, email: str, password: str) -> Optional[imaplib.IMAP4_SSL]:
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(email, password)
            return mail
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return None
    
    def fetch_messages(self, mail: imaplib.IMAP4_SSL, folder: str = "INBOX", limit: int = 10) -> List[Dict]:
        messages = []
        try:
            mail.select(folder)
            _, message_ids = mail.search(None, "ALL")
            id_list = message_ids[0].split()
            
            for msg_id in id_list[-limit:]:
                _, data = mail.fetch(msg_id, "(RFC822)")
                if data and data[0]:
                    raw_email = data[0][1]
                    msg = email_lib.message_from_bytes(raw_email)
                    
                    subject = msg["Subject"] or ""
                    sender = msg["From"] or ""
                    date = msg["Date"] or ""
                    
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode()
                                break
                    else:
                        body = msg.get_payload(decode=True).decode()
                    
                    messages.append({
                        "id": msg_id.decode(),
                        "subject": subject,
                        "from": sender,
                        "date": date,
                        "body": body[:500]
                    })
        except Exception as e:
            self.logger.error(f"Fetch messages error: {e}")
        
        return messages
    
    def get_verification_code(self, email: str, password: str, subject_contains: str = "", max_wait: int = 120) -> Optional[str]:
        import re
        mail = self.connect(email, password)
        if not mail:
            return None
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            messages = self.fetch_messages(mail)
            for msg in messages:
                subject = msg.get("subject", "")
                if subject_contains and subject_contains.lower() not in subject.lower():
                    continue
                
                body = msg.get("body", "")
                codes = re.findall(r'\b\d{6}\b', body)
                if codes:
                    mail.logout()
                    return codes[0]
                codes = re.findall(r'\b\d{4}\b', body)
                if codes:
                    mail.logout()
                    return codes[0]
            
            time.sleep(5)
        
        mail.logout()
        return None
    
    def execute(self) -> TaskResult:
        self.logger.info("Gmail client is a utility class for receiving emails")
        self.logger.info("Use this with other registration tasks that need email verification")
        
        return TaskResult(
            task_id=self.config.task_id,
            status=TaskStatus.SKIPPED,
            message="Gmail client is a utility class. Use with other tasks that need email verification."
        )


class GmailIMAPTask(BaseTask):
    def __init__(self, config: TaskConfig, global_config: Dict):
        super().__init__(config, global_config)
    
    def validate(self) -> bool:
        return True
    
    def execute(self) -> TaskResult:
        self.logger.info("Gmail IMAP task - configure with existing Gmail credentials")
        
        return TaskResult(
            task_id=self.config.task_id,
            status=TaskStatus.SKIPPED,
            message="Gmail IMAP task requires pre-configured Gmail credentials"
        )
