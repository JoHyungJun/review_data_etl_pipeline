"""
base_api_response.py
--------------------

HTTP API 에서 애플리케이션 프로세스가 응답하는 기본 response 형태를 정의한 response DTO 관련 추상 클래스 모듈
"""


from pydantic import BaseModel


class BaseApiResponse(BaseModel):
    message: str


class BaseSuccessApiResponse(BaseApiResponse):
    pass


class BaseFailedApiResponse(BaseApiResponse):
    pass
