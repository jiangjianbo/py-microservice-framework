"""
数据库配置模块

定义数据库配置类，用于配置SQLAlchemy引擎和连接池。
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DatabaseConfig:
    """
    数据库配置
    
    包含数据库连接、池化、日志等配置信息。
    支持同步和异步数据库引擎。
    """
    
    url: str  # 数据库连接URL
    async_engine: bool = False  # 是否使用异步引擎
    echo: bool = False  # 是否输出SQL日志
    pool_size: int = 5  # 连接池大小
    max_overflow: int = 10  # 最大溢出连接数
    pool_timeout: int = 30  # 连接池超时时间（秒）
    pool_recycle: int = 3600  # 连接回收时间（秒）
    pool_pre_ping: bool = True  # 连接前检测
    expunge_on_commit: bool = False  # 提交后过期
    future: bool = True  # 使用SQLAlchemy 2.0 API
    
    def get_engine_options(self) -> dict:
        """
        获取引擎配置选项
        
        Returns:
            引擎配置字典
        """
        # 检查是否为SQLite，避免使用不支持的参数
        is_sqlite = "sqlite" in self.url
        
        base_options = {
            "echo": self.echo,
        }
        
        if not is_sqlite:
            base_options.update({
                "pool_size": self.pool_size,
                "max_overflow": self.max_overflow,
                "pool_timeout": self.pool_timeout,
                "pool_recycle": self.pool_recycle,
                "pool_pre_ping": self.pool_pre_ping,
            })
        
        return base_options
    
    def get_async_engine_options(self) -> dict:
        """
        获取异步引擎配置选项
        
        Returns:
            异步引擎配置字典
        """
        options = self.get_engine_options()
        
        # 异步引擎特定的选项
        options["echo"] = self.echo
        
        return options