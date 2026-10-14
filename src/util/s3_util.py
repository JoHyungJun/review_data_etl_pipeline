"""
s3_util.py
----------

s3 관련 util 모듈
"""


from pathlib import Path
from typing import Union
from urllib.parse import urlparse

import boto3

from util.path_util import get_or_create_directory


def download_from_s3_to_directory(
        s3_uri: str,
        target_directory_path: Union[Path, str],
) -> None:
    """
    파라미터로 전달된 S3 uri 에 접근하여 파일을 로컬 디렉토리로 다운로드

    :param s3_uri: 다운로드 대상 S3 uri str
    :param target_directory_path: 다운로드 대상 로컬 디렉터리 경로 Union[Path, str]
    :return: 없음
    """

    # 파라미터 검증 및 파싱
    parsed_s3_uri = urlparse(s3_uri)
    target_directory_path = Path(target_directory_path)

    if parsed_s3_uri.scheme != "s3" or not parsed_s3_uri.netloc:
        raise ValueError(
            f"올바르지 않은 S3 URI입니다: {s3_uri}"
        )

    # 경로 관련 작업
    bucket_name = parsed_s3_uri.netloc
    prefix = parsed_s3_uri.path.lstrip("/")

    if prefix and not prefix.endswith("/"):
        prefix += "/"

    target_directory_path = get_or_create_directory(
        full_path=target_directory_path
    )

    # S3 관련 작업
    s3_client = boto3.client("s3")

    # 파라미터로 들어온 uri 경로 하위 여러 파일에 모두 접근하기 위해
    # list_objects_v2 (S3 버킷에 저장된 객체 목록 반환) AWS API 를 활용한 paginator 객체 선언
    paginator = s3_client.get_paginator("list_objects_v2")

    downloaded_file_count = 0

    for page in paginator.paginate(
        Bucket=bucket_name,
        Prefix=prefix,
    ):
        # 개별 객체의 정보가 담긴 page 에서 정보 추출 (page 에는 {"Contents": {"Key"...}} 와 같은 json 정보가 담김)
        for s3_object in page.get("Contents", []):
            # 개별 객체의 식별자 (uri)
            object_key = s3_object["Key"]

            # 디렉터리 표기용 빈 객체는 continue
            if object_key.endswith("/"):
                continue

            # 다운로드될 로컬 디렉토리 구조 세팅 (파라미터로 들어온 디렉토리 하위의 디렉토리 생성)
            relative_key = object_key[len(prefix):]

            local_path = target_directory_path / relative_key
            local_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            s3_client.download_file(
                Bucket=bucket_name,
                Key=object_key,
                Filename=str(local_path),
            )

            downloaded_file_count += 1

    if downloaded_file_count == 0:
        raise FileNotFoundError(
            f"해당 S3 uri 에서 아무 파일도 찾을 수 없습니다. S3 혹은 코드를 확인해주세요. : {s3_uri}"
        )
