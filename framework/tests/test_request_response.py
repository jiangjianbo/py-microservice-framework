"""
服务契约模块单元测试

测试服务请求和响应的各种场景和边界情况。
"""

import pytest
from serviceframework.contract.request import ServiceRequest
from serviceframework.contract.response import ServiceResponse
from serviceframework.contract.service import ServiceError, ServiceContext, ServiceMetadata
from dataclasses import dataclass


class TestServiceRequest:
    
    def test_request_creation(self):
        """测试请求对象创建"""
        request = ServiceRequest(
            service_name="user-service",
            method="get_user",
            args=(123,),
            kwargs={"include_profile": True}
        )
        assert request.service_name == "user-service"
        assert request.method == "get_user"
        assert request.args == (123,)
        assert request.kwargs["include_profile"] is True
    
    def test_request_with_default_context(self):
        """测试请求对象使用默认上下文"""
        request = ServiceRequest(
            service_name="user-service",
            method="get_user"
        )
        assert request.context is not None
        assert request.context.service_name == "user-service"
        assert request.context.method == "get_user"
    
    def test_request_validation_empty_service_name(self):
        """测试请求验证：服务名称为空"""
        with pytest.raises(ValueError, match="服务名称不能为空"):
            ServiceRequest(service_name="", method="get_user")
    
    def test_request_validation_empty_method(self):
        """测试请求验证：方法名为空"""
        with pytest.raises(ValueError, match="方法名不能为空"):
            ServiceRequest(service_name="user-service", method="")
    
    def test_request_with_context(self):
        """测试请求对象使用指定上下文"""
        context = ServiceContext(
            service_name="user-service",
            method="get_user",
            request_id="req-123",
            metadata={"user_id": 123}
        )
        request = ServiceRequest(
            service_name="user-service",
            method="get_user",
            context=context
        )
        assert request.context.request_id == "req-123"
        assert request.context.metadata["user_id"] == 123
    
    def test_request_with_context_method(self):
        """测试使用with_context创建新上下文"""
        request = ServiceRequest(
            service_name="user-service",
            method="get_user"
        )
        new_context = ServiceContext(
            service_name="user-service",
            method="get_user",
            request_id="req-456"
        )
        new_request = request.with_context(new_context)
        assert new_request.context.request_id == "req-456"
        assert new_request.service_name == request.service_name
    
    def test_request_with_args_method(self):
        """测试使用with_args创建新参数"""
        request = ServiceRequest(
            service_name="user-service",
            method="get_user"
        )
        new_request = request.with_args(456, include_profile=False)
        assert new_request.args == (456,)
        assert new_request.kwargs["include_profile"] is False
    
    def test_request_to_dict(self):
        """测试请求对象转换为字典"""
        context = ServiceContext(
            service_name="user-service",
            method="get_user",
            request_id="req-123"
        )
        request = ServiceRequest(
            service_name="user-service",
            method="get_user",
            args=(123,),
            kwargs={"include_profile": True},
            context=context,
            timeout=10.0
        )
        data = request.to_dict()
        assert data["service_name"] == "user-service"
        assert data["method"] == "get_user"
        assert data["args"] == (123,)
        assert data["kwargs"]["include_profile"] is True
        assert data["context"]["request_id"] == "req-123"
        assert data["timeout"] == 10.0
    
    def test_request_from_dict(self):
        """测试从字典创建请求对象"""
        data = {
            "service_name": "user-service",
            "method": "get_user",
            "args": [123],
            "kwargs": {"include_profile": True},
            "context": {
                "service_name": "user-service",
                "method": "get_user",
                "request_id": "req-123",
                "metadata": {"user_id": 123}
            },
            "timeout": 10.0
        }
        request = ServiceRequest.from_dict(data)
        assert request.service_name == "user-service"
        assert request.method == "get_user"
        assert request.args == (123,)
        assert request.context.request_id == "req-123"
        assert request.context.metadata["user_id"] == 123


class TestServiceResponse:
    
    def test_success_response_creation(self):
        """测试成功响应创建"""
        response = ServiceResponse.success_response(
            data={"id": 123, "name": "Alice"},
            metadata={"execution_time": 0.5}
        )
        assert response.success is True
        assert response.data["id"] == 123
        assert response.metadata["execution_time"] == 0.5
    
    def test_error_response_creation(self):
        """测试错误响应创建"""
        error = ServiceError("User not found", code="USER_NOT_FOUND")
        response = ServiceResponse.error_response(error)
        assert response.success is False
        assert response.error.code == "USER_NOT_FOUND"
        assert response.error.message == "User not found"
    
    def test_response_validation_success_with_error(self):
        """测试响应验证：成功响应包含错误"""
        error = ServiceError("Test error")
        with pytest.raises(ValueError, match="成功的响应不能包含错误信息"):
            ServiceResponse(success=True, error=error)
    
    def test_response_validation_failure_without_error(self):
        """测试响应验证：失败响应不包含错误"""
        with pytest.raises(ValueError, match="失败的响应必须包含错误信息"):
            ServiceResponse(success=False, error=None)
    
    def test_get_data_success(self):
        """测试获取数据：成功响应"""
        response = ServiceResponse.success_response(data={"id": 123})
        data = response.get_data()
        assert data["id"] == 123
    
    def test_get_data_failure(self):
        """测试获取数据：失败响应抛出异常"""
        error = ServiceError("User not found")
        response = ServiceResponse.error_response(error)
        with pytest.raises(ServiceError, match="User not found"):
            response.get_data()
    
    def test_get_data_or_default_success(self):
        """测试获取数据或默认值：成功响应"""
        response = ServiceResponse.success_response(data={"id": 123})
        data = response.get_data_or_default({"id": 0})
        assert data["id"] == 123
    
    def test_get_data_or_default_failure(self):
        """测试获取数据或默认值：失败响应返回默认值"""
        error = ServiceError("User not found")
        response = ServiceResponse.error_response(error)
        data = response.get_data_or_default({"id": 0})
        assert data["id"] == 0
    
    def test_response_to_dict_success(self):
        """测试响应转换为字典：成功响应"""
        response = ServiceResponse.success_response(
            data={"id": 123},
            metadata={"execution_time": 0.5}
        )
        data = response.to_dict()
        assert data["success"] is True
        assert data["data"]["id"] == 123
        assert data["metadata"]["execution_time"] == 0.5
        assert data["error"] is None
    
    def test_response_to_dict_failure(self):
        """测试响应转换为字典：失败响应"""
        error = ServiceError("User not found", code="USER_NOT_FOUND")
        response = ServiceResponse.error_response(error)
        data = response.to_dict()
        assert data["success"] is False
        assert data["error"]["code"] == "USER_NOT_FOUND"
        assert data["error"]["message"] == "User not found"
        assert data["data"] is None
    
    def test_response_from_dict_success(self):
        """测试从字典创建响应：成功响应"""
        data = {
            "success": True,
            "data": {"id": 123},
            "metadata": {"execution_time": 0.5}
        }
        response = ServiceResponse.from_dict(data)
        assert response.success is True
        assert response.data["id"] == 123
        assert response.metadata["execution_time"] == 0.5
    
    def test_response_from_dict_failure(self):
        """测试从字典创建响应：失败响应"""
        data = {
            "success": False,
            "error": {
                "code": "USER_NOT_FOUND",
                "message": "User not found",
                "details": {"user_id": 123}
            },
            "metadata": {"execution_time": 0.1}
        }
        response = ServiceResponse.from_dict(data)
        assert response.success is False
        assert response.error.code == "USER_NOT_FOUND"
        assert response.error.details["user_id"] == 123
    
    def test_response_generic_type(self):
        """测试响应泛型类型"""
        class User:
            def __init__(self, id: int, name: str):
                self.id = id
                self.name = name
        
        user = User(123, "Alice")
        response = ServiceResponse[User](success=True, data=user)
        assert isinstance(response.data, User)
        assert response.data.id == 123
        assert response.data.name == "Alice"