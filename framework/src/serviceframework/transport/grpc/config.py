"""
gRPC配置模块

定义gRPC传输配置，支持安全连接和性能调优。
"""

from dataclasses import dataclass


@dataclass
class GrpcConfig:
    """
    gRPC配置类
    
    配置gRPC客户端和服务器，包括主机、端口、SSL等。
    """
    host: str  # 主机地址
    port: int  # 端口号
    max_workers: int = 10  # 最大工作线程数
    timeout: int = 30  # 超时时间（秒）
    enable_ssl: bool = False  # 是否启用SSL
    cert_file: str = None  # 证书文件路径
    key_file: str = None  # 私钥文件路径
    ca_file: str = None  # CA证书文件路径
    max_message_size: int = 4 * 1024 * 1024  # 最大消息大小（4MB）
    enable_compression: bool = False  # 是否启用压缩
    
    def __post_init__(self):
        """初始化后验证"""
        if not self.host:
            raise ValueError("主机地址不能为空")
        
        if not 1 <= self.port <= 65535:
            raise ValueError("端口号必须在1到65535之间")
        
        if self.max_workers <= 0:
            raise ValueError("最大工作线程数必须大于0")
        
        if self.timeout <= 0:
            raise ValueError("超时时间必须大于0")
        
        if self.enable_ssl and not (self.cert_file and self.key_file):
            raise ValueError("启用SSL时必须提供证书文件和私钥文件")