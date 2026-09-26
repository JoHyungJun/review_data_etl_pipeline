"""
excel_storage.py
----------------

Excel 기반 개별 파일 데이터의 접근 및 관리 저장소 구현부
"""


import logging
from pathlib import Path

import duckdb as duckdb
import pandas as pd

from factory.query.duckdb_builder import DuckDBQueryBuilder
from core.base.storage.base_storage import BaseStorage
from core.base.storage.spec.base_spec import BaseStorageSpec
from core.implementation.storage.excel.spec.excel_load_spec import ExcelLoadSpec
from core.implementation.storage.excel.spec.excel_save_spec import ExcelSaveSpec
from util.logging_util import logging_file_event, logging_error_event, run_with_logging
from util.path_util import get_or_create_directory


class ExcelStorage(BaseStorage):
    """
    Excel 데이터 접근 및 관리 설정 클래스

    - 접근 대상 Excel 파일 들의 최상위 기준 경로 정보 관리
    - 데이터 관리 기본 속성 (save, load, exists) 구현
    """

    @run_with_logging()
    def save(self, save_spec: ExcelSaveSpec, df: pd.DataFrame) -> None:
        """
        파라미터로 전달된 데이터를 spec 설정에 따라 Excel 에 save

        :param save_spec: save 관련 세부 설정 정보
        :param df: save 대상 pandas.DataFrame
        :return: 없음
        """

        # pk 는 None 이 될 수 없음
        pk = save_spec.pk_column_name
        if not pk:
            logging.warning(f"[SKIP] pk={pk}: Invalid pk - pk must not be none or invalid str")
            return

        # 빈 rows 검증
        if df is None or df.empty:
            logging.warning(f"[SKIP] rows={df}: Invalid rows - rows must not be none or valid value")
            return

        # 로컬의 경우 해당 경로의 디렉토리 (root_path) 는 존재하지 않더라도 자동 생성
        get_or_create_directory(full_path=save_spec.root_path)
        full_path = save_spec.get_full_path()

        # 기존 Excel 에 save 대상 excel sheet 가 있는지 검증 및 load
        old_df = None
        if not self.exists(base_spec=save_spec):
            logging.warning(f"[MAKE] path={full_path}: File not found - create file on this path")
        else:
            try:
                old_df = pd.read_excel(
                    full_path,
                    sheet_name=save_spec.sheet_name,
                    engine="openpyxl",
                )

            # sheet 없음
            except ValueError:
                logging.warning(f"[MAKE] path={full_path}, sheet_name={save_spec.sheet_name}: "
                                f"Sheet not found - create sheet on this file")

            # 비정상적인 파일 (파일 깨짐), 포맷 오류, pandas 내부 오류 등
            # 이 경우 기존 파일을 삭제하고 새로운 파일로 save
            except Exception as e:
                # 🔥 핵심: 파일 깨짐 / 포맷 오류 / pandas 내부 오류
                logging.warning(
                    f"[WARN] path={full_path}: "
                    f"Invalid or corrupted excel file detected - {str(e)}"
                )

                try:
                    Path(full_path).unlink(missing_ok=True)
                    logging_file_event(
                        file_path=full_path,
                        log_prefix="DELETE",
                        log_message="Delete Invalid or corrupted excel file"
                    )
                except Exception as delete_error:
                    logging_file_event(
                        file_path=full_path,
                        log_prefix="DELETE",
                        log_metadata={
                            "error_message": str(delete_error),
                        },
                        log_message="Fail to delete Invalid or corrupted excel file",
                        log_level="error",
                    )

        new_df = df.copy()
        merged_df = pd.DataFrame()

        # 개별 df 에 pk 검증
        if old_df is not None and pk not in old_df.columns:
            logging.warning(f"[SAVE] target={full_path}, columns={old_df.columns}, pk={pk}: "
                            f"PK column not found in existing file - can't save without pk column, exit process")
            return
        if pk not in new_df.columns:
            logging.warning(f"[SAVE] target=target_data, columns={new_df.columns}, pk={pk}: "
                            f"PK column not found in new data - can't save without pk column, exit process")
            return

        # save_spec.overwrite 에 따라 merge 전략 다르게 적용
        # 기존 Excel 파일이 없거나 데이터가 하나도 있지 않을 경우 새로운 파일로 덮어씀
        if old_df is None or old_df.empty:
            merged_df = new_df
        else:
            old_df = old_df.copy()
            new_df = new_df.copy()

            old_df[pk] = old_df[pk].astype("string")
            new_df[pk] = new_df[pk].astype("string")

            duplicated_pks = list(set(old_df[pk]) & set(new_df[pk]))

            # overwrite true - 같은 pk 데이터의 경우 새로운 데이터가 우선 순위 (새로운 데이터로 덮어씀)
            if save_spec.overwrite:
                merged_df = pd.concat(
                    [old_df[~old_df[pk].isin(new_df[pk])], new_df],
                    ignore_index=True,
                )
            # overwrite false - 같은 pk 데이터의 경우 기존 데이터가 우선 순위 (기존 데이터로 덮어씀)
            else:
                merged_df = pd.concat(
                    [old_df, new_df[~new_df[pk].isin(old_df[pk])]],
                )

            if duplicated_pks:
                logging.debug(f"[MERGE] process=save, resource_name={save_spec.resource_name}, "
                              f"overwrite={save_spec.overwrite}, duplicated_count={len(duplicated_pks)}, "
                              f"duplicated_pks[:10]={duplicated_pks[:10]}: "
                              f"Found duplicated pks")

        with pd.ExcelWriter(full_path, engine="openpyxl", mode="w") as writer:
            merged_df.to_excel(
                writer,
                sheet_name=save_spec.sheet_name,
                index=False,
            )

        logging_file_event(
            file_path=full_path,
            log_prefix="SAVE",
            log_metadata={
                "overwrite": save_spec.overwrite,
                "sheet_name": save_spec.sheet_name,
            },
            df=df,
        )

    @run_with_logging()
    def load(self, load_spec: ExcelLoadSpec) -> pd.DataFrame:
        """
        spec 설정에 따른 대상 데이터를 Excel 에서 추출 후 반환

        주의 사항
        - 파라미터로 전달된 path 가 존재하지 않을 경우 빈 DataFrame 을 반환하기 때문에,
          해당 경로 검증 여부는 해당 메서드의 호출부가 책임을 가짐

        :param load_spec: load 관련 세부 정보 설정값을 가진 ExcelLoadSpec
        :return: spec 설정에 맞는 load 대상 데이터 pandas.DataFrame
        """

        full_path = load_spec.get_full_path()

        if not full_path.exists():
            logging_file_event(
                file_path=full_path,
                log_prefix="LOAD",
                log_metadata={
                    "process": "load",
                },
                log_message=f"Invalid path - return empty dataframe",
                log_level="warning",
            )
            logging.warning("[SKIP] File not found - return empty dataframe")
            return pd.DataFrame()

        # duck db 연결 객체
        with duckdb.connect(database=":memory:") as duckdb_connect:
            duckdb_connect.execute("LOAD excel;")

            # 어떤 시트를 load 할지 결정
            sheet_names = load_spec.sheet_names

            # 타겟 시트명 들을 추출
            if sheet_names == "*":
                with pd.ExcelFile(full_path) as xls:
                    target_sheets = xls.sheet_names
            elif isinstance(sheet_names, str):
                target_sheets = [sheet_names]
            else:
                target_sheets = sheet_names

            rows = []

            # 개별 시트 쿼리 적용 및 load
            for sheet in target_sheets:
                try:
                    load_query = DuckDBQueryBuilder.build_excel_load_query(
                        file_path=full_path,
                        sheet_name=sheet,
                        query_spec=load_spec.load_query_spec,
                    )
                    sheet_df = duckdb_connect.execute(load_query).df()
                except Exception as e:
                    logging_error_event(
                        exception_instance=e,
                        log_message="Not found sheet in this file",
                        log_metadata={
                            "path": full_path,
                            "sheet_name": sheet,
                        },
                        log_message_detail=str(e),
                    )
                    raise

                rows.append(sheet_df)

                logging_file_event(
                    file_path=full_path,
                    log_prefix="LOAD",
                    log_metadata={
                        "sheet_name": sheet,
                        "query": load_query,
                        "rows_count": len(sheet_df)
                    },
                )

            # row empty
            if not rows:
                return pd.DataFrame()

            logging_file_event(
                file_path=full_path,
                log_prefix="LOAD",
                log_metadata={
                    "sheets_name": load_spec.sheet_names,
                    "query": load_spec.load_query_spec,
                },
            )

            return pd.concat(rows, ignore_index=True)


    def exists(self, base_spec: BaseStorageSpec) -> bool:
        """
        spec 에 정의된 경로의 파일 존재 여부

        :return: spec 에 정의된 경로의 파일 존재 여부 bool
        """

        return base_spec.get_full_path().exists()
