from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, ForeignKey, Table, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

# Association table for workspace members
workspace_members = Table(
    'workspace_members',
    Base.metadata,
    Column('user_id', String, ForeignKey('user.id')),
    Column('workspace_id', String, ForeignKey('workspace.id'))
)

# Association table for worker pools
worker_pool_workers = Table(
    'worker_pool_workers',
    Base.metadata,
    Column('pool_id', String, ForeignKey('worker_pool.id')),
    Column('worker_id', String, ForeignKey('worker.id'))
)


class User(Base):
    __tablename__ = "user"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    workspaces = relationship("Workspace", secondary=workspace_members)


class Workspace(Base):
    __tablename__ = "workspace"
    id = Column(String, primary_key=True)
    name = Column(String, index=True)
    owner_id = Column(String, ForeignKey('user.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    members = relationship("User", secondary=workspace_members)
    jobs = relationship("TestJob", back_populates="workspace")
    workers = relationship("Worker", back_populates="workspace")
    pools = relationship("WorkerPool", back_populates="workspace")


class TestJob(Base):
    __tablename__ = "test_job"
    id = Column(String, primary_key=True)
    workspace_id = Column(String, ForeignKey('workspace.id'))
    user_id = Column(String, ForeignKey('user.id'))
    test_file = Column(String)
    status = Column(String, index=True)
    exit_code = Column(Integer, nullable=True)
    logs = Column(Text)
    screenshots = Column(Text)
    traces = Column(Text)
    browser = Column(String, default="chrome")
    device = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    workspace = relationship("Workspace", back_populates="jobs")
    reports = relationship("TestReport", back_populates="job")


class TestReport(Base):
    __tablename__ = "test_report"
    id = Column(String, primary_key=True)
    job_id = Column(String, ForeignKey('test_job.id'))
    allure_path = Column(String)
    html_report = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    job = relationship("TestJob", back_populates="reports")


class Worker(Base):
    __tablename__ = "worker"
    id = Column(String, primary_key=True)
    workspace_id = Column(String, ForeignKey('workspace.id'))
    name = Column(String)
    provider = Column(String)  # local, docker, railway, aws, gcp
    endpoint = Column(String)
    status = Column(String, default="online")
    cpu_cores = Column(Integer, default=2)
    memory_gb = Column(Integer, default=4)
    current_jobs = Column(Integer, default=0)
    max_jobs = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.utcnow)
    workspace = relationship("Workspace", back_populates="workers")
    pools = relationship("WorkerPool", secondary=worker_pool_workers)


class WorkerPool(Base):
    __tablename__ = "worker_pool"
    id = Column(String, primary_key=True)
    workspace_id = Column(String, ForeignKey('workspace.id'))
    name = Column(String)
    min_workers = Column(Integer, default=1)
    max_workers = Column(Integer, default=5)
    auto_scale = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    workspace = relationship("Workspace", back_populates="pools")
    workers = relationship("Worker", secondary=worker_pool_workers)


class BrowserMatrix(Base):
    __tablename__ = "browser_matrix"
    id = Column(String, primary_key=True)
    workspace_id = Column(String, ForeignKey('workspace.id'))
    name = Column(String)
    browsers = Column(String)  # JSON: ["chrome", "firefox", "safari"]
    devices = Column(String)   # JSON: ["desktop", "mobile", "tablet"]
    created_at = Column(DateTime, default=datetime.utcnow)


class BillingRecord(Base):
    __tablename__ = "billing_record"
    id = Column(String, primary_key=True)
    workspace_id = Column(String, ForeignKey('workspace.id'))
    job_count = Column(Integer)
    worker_hours = Column(Integer)
    total_cost = Column(Integer)  # in cents
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
