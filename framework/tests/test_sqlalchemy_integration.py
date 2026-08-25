"""
SQLAlchemy集成模块单元测试

测试数据库拦截器和ORM集成功能。
"""

import pytest
import asyncio as asyncio_lib
from unittest.mock import Mock, patch, MagicMock
from serviceframework.database.interceptor import DatabaseInterceptor, DatabaseConfig
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import async_sessionmaker
from dataclasses import dataclass


Base = declarative_base()


class TestDatabaseConfig:
    
    def test_config_creation(self):
        """测试数据库配置创建"""
        config = DatabaseConfig(
            url="sqlite:///:memory:",
            echo=True,
            pool_size=10,
            max_overflow=20
        )
        
        assert config.url == "sqlite:///:memory:"
        assert config.echo is True
        assert config.pool_size == 10
        assert config.max_overflow == 20


class TestDatabaseInterceptor:
    
    def test_interceptor_creation(self):
        """测试数据库拦截器创建"""
        config = DatabaseConfig(url="sqlite:///:memory:")
        interceptor = DatabaseInterceptor(config)
        
        assert interceptor.config == config
        assert interceptor._engine is None
    
    def test_interceptor_engine_creation_sync(self):
        """测试同步数据库引擎创建"""
        config = DatabaseConfig(url="sqlite:///:memory:")
        interceptor = DatabaseInterceptor(config)
        
        interceptor.setup_engine()
        
        assert interceptor._engine is not None
        assert interceptor._session_factory is not None
    
    def test_interceptor_engine_creation_async(self):
        """测试异步数据库引擎创建"""
        config = DatabaseConfig(
            url="sqlite+aiosqlite:///:memory:",
            async_engine=True
        )
        interceptor = DatabaseInterceptor(config)
        
        async def setup():
            interceptor.setup_engine()
            assert interceptor._async_engine is not None
            assert interceptor._async_session_factory is not None
        
        asyncio_lib.run(setup())
    
    def test_interceptor_setup_model(self):
        """测试模型设置"""
        config = DatabaseConfig(url="sqlite:///:memory:")
        interceptor = DatabaseInterceptor(config)
        interceptor.setup_engine()
        
        class User(Base):
            __tablename__ = "users"
            __table_args__ = {"extend_existing": True}
            id = Column(Integer, primary_key=True)
            name = Column(String(50))
        
        interceptor.setup_model(Base)
        
        # 检查表是否创建
        with interceptor._engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'"))
            assert result.fetchone() is not None
    
    def test_interceptor_session_creation(self):
        """测试会话创建"""
        config = DatabaseConfig(url="sqlite:///:memory:")
        interceptor = DatabaseInterceptor(config)
        interceptor.setup_engine()
        
        class User(Base):
            __tablename__ = "users"
            __table_args__ = {"extend_existing": True}
            id = Column(Integer, primary_key=True)
            name = Column(String(50))
        
        interceptor.setup_model(Base)
        
        session = interceptor.create_session()
        
        assert session is not None
        
        # 使用会话
        session.add(User(name="Alice"))
        session.commit()
        
        # 验证数据
        users = session.query(User).all()
        assert len(users) == 1
        assert users[0].name == "Alice"
        
        session.close()
    
    def test_interceptor_close(self):
        """测试拦截器关闭"""
        config = DatabaseConfig(url="sqlite:///:memory:")
        interceptor = DatabaseInterceptor(config)
        interceptor.setup_engine()
        
        class User(Base):
            __tablename__ = "users"
            __table_args__ = {"extend_existing": True}
            id = Column(Integer, primary_key=True)
            name = Column(String(50))
        
        interceptor.setup_model(Base)
        
        # 创建会话
        session = interceptor.create_session()
        session.close()
        
        # 关闭拦截器
        interceptor.close()
        
        assert interceptor._engine is None
        assert interceptor._session_factory is None
    
    def test_interceptor_health_check(self):
        """测试数据库健康检查"""
        config = DatabaseConfig(url="sqlite:///:memory:")
        interceptor = DatabaseInterceptor(config)
        
        # 未设置引擎时应该返回False
        assert interceptor.health_check() is False
        
        interceptor.setup_engine()
        
        # 设置引擎后应该返回True
        assert interceptor.health_check() is True
        
        interceptor.close()
    
    def test_interceptor_get_session_info(self):
        """测试获取会话信息"""
        config = DatabaseConfig(url="sqlite:///:memory:")
        interceptor = DatabaseInterceptor(config)
        interceptor.setup_engine()
        
        info = interceptor.get_session_info()
        
        assert info is not None
        assert "engine" in info
        assert "url" in info
        assert "pool_size" in info
        
        interceptor.close()
    
    def test_interceptor_health_check_after_close(self):
        """测试关闭后健康检查"""
        config = DatabaseConfig(url="sqlite:///:memory:")
        interceptor = DatabaseInterceptor(config)
        interceptor.setup_engine()
        
        assert interceptor.health_check() is True
        
        interceptor.close()
        
        assert interceptor.health_check() is False