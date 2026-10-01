"""
application.py
--------------

FastAPI 객체 및 개별 router 조립 모듈
"""


from fastapi import FastAPI

from entry.deploy.config.api.router.pipeline import pipeline_router


application = FastAPI()

application.include_router(pipeline_router)
