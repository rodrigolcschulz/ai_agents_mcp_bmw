"""
Database models for the AI Data Engineering project
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class BMWSales(Base):
    """BMW Sales data model"""
    __tablename__ = 'bmw_sales'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    year_month = Column(String(7), nullable=True)  # Format: YYYY-MM
    region = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    sales_units = Column(Integer, nullable=True)
    revenue = Column(Float, nullable=True)
    total_sales = Column(Float, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<BMWSales(year={self.year}, month={self.month}, region={self.region}, sales_units={self.sales_units})>"

class DataSource(Base):
    """Data source tracking model"""
    __tablename__ = 'data_sources'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    source_type = Column(String(50), nullable=False)  # 'kaggle', 'api', 'file'
    source_url = Column(String(500), nullable=True)
    dataset_name = Column(String(200), nullable=True)
    file_path = Column(String(500), nullable=True)
    record_count = Column(Integer, nullable=True)
    last_updated = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<DataSource(name={self.name}, type={self.source_type}, records={self.record_count})>"

class QueryLog(Base):
    """Query logging for AI agent interactions"""
    __tablename__ = 'query_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_query = Column(Text, nullable=False)
    sql_query = Column(Text, nullable=True)
    response = Column(Text, nullable=True)
    execution_time = Column(Float, nullable=True)  # in seconds
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    user_id = Column(String(100), nullable=True)
    session_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<QueryLog(query={self.user_query[:50]}..., success={self.success}, time={self.execution_time})>"

class SystemMetrics(Base):
    """System performance and usage metrics"""
    __tablename__ = 'system_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20), nullable=True)
    tags = Column(Text, nullable=True)  # JSON string for additional metadata
    recorded_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<SystemMetrics(name={self.metric_name}, value={self.metric_value}, unit={self.metric_unit})>"
