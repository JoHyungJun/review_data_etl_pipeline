"""
s3_storage.py
-------------

S3 기반 개별 파일 데이터의 접근 및 관리 저장소 구현부
"""


import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Union

import boto3
import duckdb
import pandas as pd
from botocore.exceptions import ClientError

from core.base.storage.base_storage import BaseStorage
from core.implementation.storage.s3.spec.s3_load_spec import S3LoadSpec
from core.implementation.storage.s3.spec.s3_save_spec import S3SaveSpec
from factory.query.duckdb_builder import DuckDBQueryBuilder
from util.logging_util import run_with_logging, logging_file_event


class S3Storage(BaseStorage):
    """
    S3 데이터 접근 및 관리 설정 클래스

    - 접근 대상 S3 파일 들의 최상위 기준 경로 정보 관리
    - 데이터 관리 기본 속성 (save, load, exists) 구현
    - S3 데이터 저장 형식은 parquet
    """

    def __init__(self) -> None:
        # S3 연결 객체 초기화
        self._s3_client = boto3.client("s3")

    @run_with_logging()
    def save(
            self,
            save_spec: S3SaveSpec,
            df: pd.DataFrame
    ) -> None:
        """
        파라미터로 전달된 dataframe 데이터를 spec 설정에 따라 S3 Object 로 save

        :param save_spec: save 관련 세부 설정 정보
        :param df: save 대상 pandas.DataFrame
        :return: 없음
        """

        # pk 는 None 이 될 수 없음
        pk = save_spec.pk_key_name
        if not pk:
            logging.warning(f"[SKIP] pk={pk}: Invalid pk - pk must not be none or invalid str")
            return

        # 빈 rows 검증
        if df is None or df.empty:
            logging.warning(f"[SKIP] rows={df}: Invalid rows - rows must not be none or valid value")
            return

        # 데이터 경로 식별자 정보 추출
        bucket_name = save_spec.bucket_name
        object_key = save_spec.get_full_path().as_posix()
        full_path = save_spec.get_full_path()

        new_df = df.copy()
        merged_df = pd.DataFrame()
        old_df = self.load(
            S3LoadSpec(
                root_path=save_spec.root_path,
                resource_name=save_spec.resource_name,
                bucket_name=bucket_name,
            )
        )

        # 개별 df 에 pk 검증
        if old_df is not None and pk not in old_df.columns:
            logging.warning(f"[SAVE] target={full_path}, columns={old_df.columns}, pk={pk}: "
                            f"PK key not found in parquet data - can't save without pk column, exit process")
            return
        if pk not in new_df.columns:
            logging.warning(f"[SAVE] target=target_data, columns={new_df.columns}, pk={pk}: "
                            f"PK key not found in new parquet data - can't save without pk column, exit process")
            return

        # save_spec.overwrite 에 따라 merge 전략 다르게 적용
        # 기존 파일이 없거나, 접근에서 에러가 발생하거나, 데이터가 하나도 있지 않은 경우 새로운 파일로 덮어씀
        if old_df is None or old_df.empty:
            merged_df = new_df
        else:
            old_df[pk] = old_df[pk].astype("string")
            new_df[pk] = new_df[pk].astype("string")

            duplicated_pks = list(set(old_df[pk]) & set(new_df[pk]))

            # overwrite true - 같은 pk 데이터의 경우 새로운 데이터가 우선 순위 (새로운 데이터로 덮어씀)
            if save_spec.overwrite:
                merged_df = pd.concat(
                [
                        old_df[~old_df[pk].isin(new_df[pk])],
                        new_df
                    ],
                    ignore_index=True,
                )
            # overwrite false - 같은 pk 데이터의 경우 기존 데이터가 우선 순위 (기존 데이터로 덮어씀)
            else:
                merged_df = pd.concat(
                [
                        old_df,
                        new_df[~new_df[pk].isin(old_df[pk])]
                    ],
                    ignore_index=True,
                )

            if duplicated_pks:
                logging.debug(f"[MERGE] process=save, resource_name={full_path}, "
                              f"overwrite={save_spec.overwrite}, duplicated_count={len(duplicated_pks)}, "
                              f"duplicated_pks[:10]={duplicated_pks[:10]}: "
                              f"Found duplicated pks")

        with TemporaryDirectory() as temp_dir:
            temp_file_path = Path(temp_dir) / save_spec.resource_name

            merged_df.to_parquet(
                temp_file_path,
                engine="pyarrow",
                index=False,
            )

            self._s3_client.upload_file(
                Filename=str(temp_file_path),
                Bucket=bucket_name,
                Key=object_key,
            )

        logging_file_event(
            file_path=full_path,
            log_prefix="SAVE",
            log_metadata={
                "overwrite": save_spec.overwrite,
                "bucket_name": bucket_name,
                "object_key": object_key,
            },
            df=df,
        )

    @run_with_logging()
    def load(
            self,
            load_spec: S3LoadSpec,
    ) -> pd.DataFrame:
        """
        spec 설정에 따른 대상 데이터를 S3 Object 에서 추출 후 반환

        주의 사항
        - 대상 S3 Object 가 존재하지 않거나 접근할 수 없는 경우 빈 dataframe 을 반환하기 때문에,
          S3 연결, 권한 등 설정 검증 여부는 해당 메서드의 호출부가 책임을 가짐

        :param load_spec: load 관련 세부 정보 설정값을 가진 S3LoadSpec
        :return: spec 설정에 맞는 load 대상 데이터 pandas.DataFrame
        """

        bucket_name = load_spec.bucket_name
        object_key = load_spec.get_full_path().as_posix()

        if not self.exists(load_spec):
            logging.warning(
                f"[SKIP] bucket={bucket_name}, key={object_key}: "
                f"S3 Object not found - return empty dataframe"
            )
            return pd.DataFrame()

        with TemporaryDirectory() as temp_dir:
            temp_file_path = Path(temp_dir) / load_spec.resource_name
            from_path = temp_file_path.as_posix()

            self._s3_client.download_file(
                Bucket=bucket_name,
                Key=object_key,
                Filename=str(temp_file_path),
            )

            from_clause = (
                f"FROM read_parquet('{from_path}')"
            )

            load_query = DuckDBQueryBuilder.build_load_query(
                from_clause=from_clause,
                query_spec=load_spec.load_query_spec,
            )

            with duckdb.connect(database=":memory:") as duckdb_connect:
                loaded_df = duckdb_connect.execute(load_query).df()

        logging_file_event(
            file_path=load_spec.get_full_path(),
            log_prefix="LOAD",
            log_metadata={
                "query": load_spec.load_query_spec,
            },
        )

        return loaded_df

    def exists(
        self,
        s3_spec: Union[S3SaveSpec, S3LoadSpec],
    ) -> bool:
        """
        spec 에 정의된 경로의 파일 존재 여부

        주의 사항
        - ClientError 발생 시, 해당 메서드는 실제 파일이 존재하지 않는 경우와 권한 부족 등의 외적인 문제에 대한 구분 없이 False 반환

        :param s3_spec: S3 관련 저장소의 정보 Union[S3SaveSpec, S3LoadSpec]
        :return: spec 에 정의된 경로의 파일 존재 여부 bool
        """

        bucket_name = s3_spec.bucket_name
        object_key = s3_spec.get_full_path().as_posix()

        try:
            self._s3_client.head_object(
                Bucket=bucket_name,
                Key=object_key,
            )
            return True

        except ClientError as e:
            logging.warning(
                f"[WARN] bucket={bucket_name}, key={object_key}: "
                f"S3 Object does not exist or failed to access S3 - {str(e)}"
            )
            return False


