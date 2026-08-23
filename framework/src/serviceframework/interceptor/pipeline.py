"""
拦截器管道模块

实现拦截器链的管理和执行，按照顺序执行before方法，按逆序执行after方法。
管道负责协调拦截器的执行流程，处理异常和跳过逻辑。
"""

from typing import List, Callable, Awaitable, Any
from serviceframework.interceptor.base import ServiceInterceptor, InterceptorContext


class InterceptorPipeline:
    """
    拦截器管道
    
    管理拦截器链，按照正确的顺序执行拦截器逻辑。
    支持拦截器的添加、移除和清空，以及自定义执行逻辑。
    """
    
    def __init__(self):
        """初始化拦截器管道"""
        self._interceptors: List[ServiceInterceptor] = []
    
    def add_interceptor(self, interceptor: ServiceInterceptor) -> None:
        """
        添加拦截器
        
        Args:
            interceptor: 拦截器实例
            
        Raises:
            ValueError: 如果拦截器已存在
        """
        if interceptor in self._interceptors:
            raise ValueError("拦截器已存在")
        
        self._interceptors.append(interceptor)
    
    def remove_interceptor(self, interceptor: ServiceInterceptor) -> None:
        """
        移除拦截器
        
        Args:
            interceptor: 拦截器实例
        """
        if interceptor in self._interceptors:
            self._interceptors.remove(interceptor)
    
    def clear(self) -> None:
        """清空所有拦截器"""
        self._interceptors.clear()
    
    def get_interceptors(self) -> List[ServiceInterceptor]:
        """
        获取所有拦截器
        
        Returns:
            拦截器列表
        """
        return self._interceptors.copy()
    
    async def execute(
        self,
        context: InterceptorContext,
        target: Callable[..., Awaitable[Any]]
    ) -> Any:
        """
        执行拦截器链和目标函数
        
        Args:
            context: 拦截器上下文
            target: 目标函数
            
        Returns:
            调用结果
            
        Raises:
            Exception: 如果目标函数或拦截器抛出异常
        """
        if not self._interceptors:
            # 没有拦截器，直接执行目标
            return await target()
        
        # 执行所有before方法
        for interceptor in self._interceptors:
            await interceptor.before(context)
            
            # 如果拦截器设置了跳过标志，直接返回结果
            if context.skip_execution:
                if context.result is not None:
                    return context.result
                raise ValueError("拦截器跳过执行但未提供结果")
        
        # 执行目标函数
        result = None
        error = None
        
        try:
            result = await target()
            context.result = result
            
            # 按逆序执行after方法
            for interceptor in reversed(self._interceptors):
                await interceptor.after(context, result)
            
            return result
            
        except Exception as e:
            error = e
            context.error = error
            
            # 按逆序执行on_error方法
            for interceptor in reversed(self._interceptors):
                await interceptor.on_error(context, error)
            
            raise
    
    def count(self) -> int:
        """
        获取拦截器数量
        
        Returns:
            拦截器数量
        """
        return len(self._interceptors)
    
    def is_empty(self) -> bool:
        """
        检查管道是否为空
        
        Returns:
            如果为空返回True，否则返回False
        """
        return len(self._interceptors) == 0