"""
Litestar Web适配器模块

提供HTTP/API层的适配功能，将HTTP请求转换为服务调用。
Litestar适配器充当Web层和服务层之间的桥梁，自动处理HTTP路由、错误处理等。
"""

from typing import Dict, Optional, List, Any
from litestar import Litestar, get, post, MediaType
from litestar.status_codes import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_404_NOT_FOUND
from litestar.response import Response
from serviceframework.proxy.proxy import ServiceProxy
from serviceframework.contract.service import ServiceError


class LitestarAdapter:
    """
    Litestar Web适配器
    
    提供HTTP/API层的适配功能，将HTTP请求转换为服务调用。
    支持自动路由生成、错误处理、健康检查等功能。
    """
    
    def __init__(self):
        """初始化适配器"""
        self.app = Litestar()
        self.service_proxies: Dict[str, ServiceProxy] = {}
        self._setup_default_routes()
    
    def register_service_proxy(self, proxy: ServiceProxy) -> None:
        """
        注册服务代理
        
        Args:
            proxy: 服务代理实例
        """
        if not proxy.service_name:
            raise ValueError("服务名称不能为空")
        
        self.service_proxies[proxy.service_name] = proxy
    
    def get_service_proxy(self, service_name: str) -> ServiceProxy:
        """
        获取服务代理
        
        Args:
            service_name: 服务名称
            
        Returns:
            服务代理实例
            
        Raises:
            ValueError: 如果代理未注册
        """
        if service_name not in self.service_proxies:
            raise ValueError(f"代理'{service_name}'未注册")
        
        return self.service_proxies[service_name]
    
    async def invoke_service(
        self,
        service_name: str,
        method: str,
        *args,
        **kwargs
    ):
        """
        调用服务方法
        
        Args:
            service_name: 服务名称
            method: 方法名
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            方法调用结果
            
        Raises:
            ValueError: 如果服务未注册
            Exception: 服务调用异常
        """
        proxy = self.get_service_proxy(service_name)
        return await proxy.invoke(method, *args, **kwargs)
    
    def create_http_route(
        self,
        path: str,
        service_name: str,
        method_name: str,
        methods: List[str] = None
    ):
        """
        创建HTTP路由
        
        Args:
            path: HTTP路径
            service_name: 服务名称
            method_name: 服务方法名
            methods: 允许的HTTP方法列表
            
        Returns:
            路由处理器
        """
        if not path:
            raise ValueError("路径不能为空")
        if not service_name:
            raise ValueError("服务名称不能为空")
        if not method_name:
            raise ValueError("方法名不能为空")
        
        methods = methods or ["GET"]
        
        # 创建处理器函数
        async def handler(**kwargs: Any) -> Response:
            try:
                # 从路径参数中提取参数
                args = []
                for key, value in kwargs.items():
                    args.append(value)
                
                # 调用服务
                result = await self.invoke_service(service_name, method_name, *args)
                
                return Response(
                    content={"success": True, "data": result},
                    status_code=200,
                    media_type=MediaType.JSON
                )
            except ServiceError as e:
                return Response(
                    content={
                        "success": False,
                        "error": e.to_dict()
                    },
                    status_code=HTTP_404_NOT_FOUND,
                    media_type=MediaType.JSON
                )
            except Exception as e:
                return Response(
                    content={
                        "success": False,
                        "error": {
                            "code": "INTERNAL_ERROR",
                            "message": str(e)
                        }
                    },
                    status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                    media_type=MediaType.JSON
                )
        
        # 根据HTTP方法类型注册路由
        if "GET" in methods:
            handler_decorator = get(path)
        elif "POST" in methods:
            handler_decorator = post(path)
        else:
            raise ValueError(f"不支持的HTTP方法: {methods}")
        
        # 注册路由处理器
        route = handler_decorator(handler)
        
        # 将路由添加到应用中
        self.app.register(route)
        
        return route
    
    def _setup_default_routes(self):
        """设置默认路由"""
        
        @get("/health")
        async def health_check() -> Response:
            """健康检查端点"""
            health_data = {
                "status": "healthy",
                "services": list(self.service_proxies.keys())
            }
            
            # 检查所有服务的可用性
            service_status = {}
            for service_name, proxy in self.service_proxies.items():
                try:
                    is_available = proxy.is_available()
                    service_status[service_name] = {
                        "available": is_available,
                        "endpoint": proxy.get_endpoint()
                    }
                except Exception:
                    service_status[service_name] = {
                        "available": False,
                        "error": "健康检查失败"
                    }
            
            health_data["services_status"] = service_status
            
            return Response(
                content=health_data,
                status_code=200,
                media_type=MediaType.JSON
            )
        
        self.app.register(health_check)
    
    def get_app(self) -> Litestar:
        """
        获取Litestar应用实例
        
        Returns:
            Litestar应用实例
        """
        return self.app
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """
        运行Web服务器
        
        Args:
            host: 监听地址
            port: 监听端口
        """
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)