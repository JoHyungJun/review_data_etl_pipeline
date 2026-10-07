"""
s3_load_spec.py
---------------

S3 데이터 조회에 필요한 속성 정의 모듈
"""


from dataclasses import dataclass, field

from core.base.storage.spec.base_load_spec import BaseStorageLoadSpec


@dataclass(frozen=True)
class S3LoadSpec(BaseStorageLoadSpec):
    """
    S3 (storage) 접근 및 저장에 필요한 세부 속성 설정 관련 공통 속성 클래스

    주의 사항
    - S3 spec 이 관리하는 변수 및 활용법에 대한 설명은 다음과 같음
        - bucket_name:
            S3 데이터가 저장되는 Bucket 식별자

        - root_path:
            S3 Bucket 내부에서 Object 가 저장될 기준 경로 (prefix)
            실제 디렉토리가 존재하는 것은 아니며,
            S3 Object Key의 상위 경로를 표현하기 위한 논리적인 경로

        - resource_name:
            저장할 S3 Object 이름

      따라서 S3 Object 경로에 접근하기 위해선 get_full_path() 를 str 형태로 활용하길 권고
      (ex.
            S3 Object key : 'data/platform/output/a.xlsx' 라고 가정하면,
            root_path : 'data/platform/output'
            resource_name : 'a.xlsx'
      )
    """

    # S3 object 저장소 bucket 식별자
    bucket_name: str = field(kw_only=True)
