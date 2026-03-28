"""
SQLAlchemy 数据库模块
提供任务结果和账号的持久化存储
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class TaskStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    password = Column(String(255))
    username = Column(String(255))
    extra_data = Column(JSON, default={})
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "email": self.email,
            "password": self.password,
            "username": self.username,
            "extra_data": self.extra_data,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None
        }


class TaskResult(Base):
    __tablename__ = "task_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(100), nullable=False)
    status = Column(SQLEnum(TaskStatusEnum), nullable=False)
    message = Column(Text)
    error = Column(Text)
    duration = Column(String(50))
    screenshot_path = Column(String(500))
    data = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "status": self.status.value if self.status else None,
            "message": self.message,
            "error": self.error,
            "duration": self.duration,
            "screenshot_path": self.screenshot_path,
            "data": self.data,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Database:
    def __init__(self, db_path: str = "data/tasks.db"):
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        logger.info(f"Database initialized at {db_path}")
    
    def get_session(self) -> Session:
        return self.Session()
    
    def add_account(
        self,
        task_id: str,
        email: str,
        password: str = "",
        username: str = "",
        extra_data: Dict = None,
        status: str = "active"
    ) -> Account:
        session = self.get_session()
        try:
            account = Account(
                task_id=task_id,
                email=email,
                password=password,
                username=username,
                extra_data=extra_data or {},
                status=status
            )
            session.add(account)
            session.commit()
            logger.info(f"Account added: {email} for task {task_id}")
            return account
        finally:
            session.close()
    
    def get_accounts_by_task(self, task_id: str) -> List[Account]:
        session = self.get_session()
        try:
            return session.query(Account).filter(Account.task_id == task_id).all()
        finally:
            session.close()
    
    def get_all_accounts(self) -> List[Account]:
        session = self.get_session()
        try:
            return session.query(Account).all()
        finally:
            session.close()
    
    def add_task_result(
        self,
        task_id: str,
        status: TaskStatusEnum,
        message: str = "",
        error: str = "",
        duration: str = "",
        screenshot_path: str = "",
        data: Dict = None
    ) -> TaskResult:
        session = self.get_session()
        try:
            result = TaskResult(
                task_id=task_id,
                status=status,
                message=message,
                error=error,
                duration=duration,
                screenshot_path=screenshot_path,
                data=data or {}
            )
            session.add(result)
            session.commit()
            logger.info(f"Task result added: {task_id} - {status}")
            return result
        finally:
            session.close()
    
    def get_task_results(self, task_id: str = None, limit: int = 100) -> List[TaskResult]:
        session = self.get_session()
        try:
            query = session.query(TaskResult)
            if task_id:
                query = query.filter(TaskResult.task_id == task_id)
            return query.order_by(TaskResult.created_at.desc()).limit(limit).all()
        finally:
            session.close()
    
    def get_stats(self) -> Dict[str, Any]:
        session = self.get_session()
        try:
            total_accounts = session.query(Account).count()
            total_results = session.query(TaskResult).count()
            
            success_count = session.query(TaskResult).filter(
                TaskResult.status == TaskStatusEnum.SUCCESS
            ).count()
            failed_count = session.query(TaskResult).filter(
                TaskResult.status == TaskStatusEnum.FAILED
            ).count()
            
            return {
                "total_accounts": total_accounts,
                "total_results": total_results,
                "success_count": success_count,
                "failed_count": failed_count
            }
        finally:
            session.close()
