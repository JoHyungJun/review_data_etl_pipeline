"""
api.py
------

외부 API 통신 관련 커스텀 에러 관련 클래스 모듈
"""


class ExternalScrapingApiAuthenticationExpiredError(RuntimeError):
    """
    외부 API 를 통한 scraping 요청 중 토큰 혹은 인증 정보가 만료되어 이후의 프로세스를 진행할 수 없을 때 발생하는 에러
    """

    pass