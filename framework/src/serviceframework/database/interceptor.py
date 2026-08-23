"""
SQLAlchemy数据库拦截器模块

提供SQLAlchemy引擎管理、会话创建和拦截功能。
拦截器可以记录SQL执行、监控性能、注入追踪信息等。
"""

from typing import Optional, Any, Dict, TYPE_CHECKING, Union
from contextlib import contextmanager, asynccontextmanager
from sqlalchemy import create_engine, event, Engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import Pool
from serviceframework.interceptor.base import InterceptorContext, ServiceInterceptor
from serviceframework.database.config import DatabaseConfig
import time
import logging

if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeMeta

logger = logging.getLogger(__name__)


class DatabaseInterceptor(ServiceInterceptor):
    """
    数据库拦截器
    
    提供SQLAlchemy引擎管理、会话创建和拦截功能。
    拦截器可以记录SQL执行、监控性能、注入追踪信息等。
    """
    
    def __init__(self, config: DatabaseConfig):
        """
        初始化数据库拦截器
        
        Args:
            config: 数据库配置
        """
        self.config = config
        self._engine: Optional[Engine] = None
        self._async_engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._async_session_factory: Optional[async_sessionmaker] = None
        self._sql_history: list[Dict[str, Any]] = []
        self._setup_events()
    
    def _setup_events(self):
        """设置事件监听"""
        pass  # 事件将在setup_engine中设置
    
    def setup_engine(self) -> None:
        """
        设置数据库引擎
        
        根据配置创建同步或异步引擎，并设置连接池和事件监听。
        """
        if self.config.async_engine:
            self._async_engine = create_async_engine(
                self.config.url,
                **self.config.get_async_engine_options()
            )
            self._setup_async_events()
            
            # 创建异步会话工厂
            from sqlalchemy.ext.asyncio import async_sessionmaker
            self._async_session_factory = async_sessionmaker(
                bind=self._async_engine,
                expire_on_commit=self.config.expunge_on_commit
            )
        else:
            self._engine = create_engine(
                self.config.url,
                **self.config.get_engine_options()
            )
            self._setup_sync_events()
    
    def _setup_sync_events(self) -> None:
        """设置同步引擎事件"""
        if self._engine is None:
            return
        
        @event.listens_for(self._engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            start_time = time.time()
            context._query_start_time = start_time
        
        @event.listens_for(self._engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            if hasattr(context, "_query_start_time"):
                duration = time.time() - context._query_start_time
                self._sql_history.append({
                    "statement": statement,
                    "parameters": parameters,
                    "duration": duration,
                    "success": True
                })
        
        @event.listens_for(self._engine, "handle_error")
        def dbapi_error(conn, cursor, statement, parameters, context, exception):
            self._sql_history.append({
                "statement": statement,
                "parameters": parameters,
                "success": False,
                "error": str(exception)
            })
    
    def _setup_async_events(self) -> None:
        """设置异步引擎事件"""
        if self._async_engine is None:
            return
        
        # 异步事件设置（简化版）
        pass
    
    def setup_model(self, base: "DeclarativeMeta") -> None:
        """
        设置模型基类
        
        Args:
            base: SQLAlchemy声明式基类
        """
        if self.config.async_engine and self._async_engine is not None:
            # 异步引擎设置
            async def setup_async():
                async with self._async_engine.begin() as conn:
                    await conn.run_sync(base.metadata.create_all)
            
            import asyncio
            asyncio.run(setup_async())
        elif self._engine is not None:
            # 同步引擎设置
            base.metadata.create_all(self._engine)
    
    def create_session(self) -> Session:
        """
        创建数据库会话
        
        Returns:
            SQLAlchemy会话对象
            
        Raises:
            RuntimeError: 如果引擎未设置
        """
        if self._engine is None:
            raise RuntimeError("数据库引擎未设置")
        
        if self._session_factory is None:
            self._session_factory = sessionmaker(bind=self._engine)
        
        return self._session_factory()
    
    @asynccontextmanager
    async def create_async_session(self) -> AsyncSession:
        """
        创建异步数据库会话（上下文管理器）

        Returns:
            SQLAlchemy异步会话对象

        Raises:
            RuntimeError: 如果异步引擎未设置
        """
        if self._async_engine is None:
            raise RuntimeError("异步数据库引擎未设置")

        if self._async_session_factory is None:
            self._async_session_factory = async_sessionmaker(
                bind=self._async_engine,
                expire_on_commit=False
            )
        async with self._async_session_factory() as session:
            yield session
    
    def close(self) -> None:
        """关闭数据库引擎和连接池"""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
        
        if self._async_engine is not None:
            import asyncio
            asyncio.run(self._async_engine.dispose())
            self._async_engine = None
            self._async_session_factory = None
    
    def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            如果数据库连接正常返回True，否则返回False
        """
        try:
            if self._engine is not None:
                with self._engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                return True
            elif self._async_engine is not None:
                import asyncio
                async def check():
                    async with self._async_engine.connect() as conn:
                        await conn.execute(text("SELECT 1"))
                        return True
                return asyncio.run(check())
            return False
        except Exception as e:
            logger.warning(f"数据库健康检查失败: {e}")
            return False
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        获取会话信息
        
        Returns:
            包含会话信息的字典
        """
        info = {
            "url": self.config.url,
            "async_engine": self.config.async_engine,
            "pool_size": self.config.pool_size,
            "max_overflow": self.config.max_overflow,
            "echo": self.config.echo,
        }
        
        if self._engine is not None:
            pool = self._engine.pool
            info["engine_status"] = "connected"
            info["pool_size"] = pool.size()
            info["checked_in_connections"] = pool.checkedout()
            info["overflow_connections"] = pool.overflow()
        elif self._async_engine is not None:
            info["async_engine_status"] = "connected"
        
        info["sql_history_count"] = len(self._sql_history)
        
        return info
    
    def get_sql_history(self) -> list[Dict[str, Any]]:
        """
        获取SQL执行历史
        
        Returns:
            SQL执行历史记录
        """
        return self._sql_history.copy()
    
    def clear_sql_history(self) -> None:
        """清空SQL执行历史"""
        self._sql_history.clear()
    
    async def before(self, context: InterceptorContext) -> None:
        """
        在服务调用前执行
        
        Args:
            context: 拦截器上下文
        """
        # 可以在服务调用前注入数据库会话
        pass
    
    async def after(self, context: InterceptorContext, result: Any) -> None:
        """
        在服务调用成功后执行
        
        Args:
            context: 拦截器上下文
            result: 调用结果
        """
        # 可以在服务调用后清理数据库会话
        pass
    
    async def on_error(self, context: InterceptorContext, error: Exception) -> None:
        """
        在服务调用失败时执行
        
        Args:
            context: 拦截器上下文
            error: 异常信息
        """
        # 可以在服务调用失败时记录错误信息到数据库
        pass