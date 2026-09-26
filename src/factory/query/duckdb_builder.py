"""
duckdb_builder.py
-----------------

duck db 환경용 쿼리문 빌더 클래스 설정 모듈
"""
import logging
from pathlib import Path
from typing import Union, Optional, Literal, OrderedDict, Sized

from core.base.query.spec.base_load_spec import BaseLoadQuerySpec
from core.base.schema.attribute.util.attribute_schema_util import validate_column_name


class DuckDBQueryBuilder:

    @staticmethod
    def _escape_identifier(column_name: str) -> str:
        """
        쿼리문 작성을 위해 파라미터로 전달된 컬럼명의 앞뒤로 큰 따옴표 (") 추가
        (ex. 컬럼명 -> "컬럼명")

        :param column_name: 큰 따옴표 추가 대상 컬럼명 str
        :return: 앞뒤로 큰 따옴표가 추가된 컬럼명 str
        """

        if column_name == "*":
            return column_name

        return f'"{column_name}"'

    @staticmethod
    def _filtering_valid_select_columns(columns: list[str]) -> list[str]:
        """
        select 대상 컬럼명 리스트 검증 및 필터링

        - None, ' ', '' 값 제외
        - 앞뒤 빈 문자열 제거 (.strip())
        - 컬럼 리스트에 와일드카드 (*) 가 있다면, 와일드카드 반환
        """

        filtered = []

        for col in columns:
            validated_column_name = validate_column_name(col)

            if validated_column_name is None:
                continue

            filtered.append(validated_column_name)

        if '*' in filtered:
            filtered = ['*']

        # 중복 컬럼 제거
        return list(dict.fromkeys(filtered))

    @staticmethod
    def build_excel_load_query(
            file_path: Union[str, Path],
            sheet_name: str,
            query_spec: Optional[BaseLoadQuerySpec],
    ) -> str:
        """
        경로 정보를 받아 전체 Excel 데이터를 load 할 쿼리를 반환

        :param file_path: Excel 경로 Union[str, Path]
        :param sheet_name: 대상 시트명 str
        :param query_spec: load 관련 쿼리 정보 Optional[BaseLoadQuerySpec]
        :return: load 전체 쿼리문 str
        """

        file_path_for_excel = str(file_path).replace("\\", "/")

        # duck db 의 타입 추론에서, 빈 셀을 DOUBLE 이 아닌 VARCHAR 로 추론하게끔 하기 위한 empty_as_varchar 설정 추가
        from_clauses = (
            f" FROM read_xlsx("
            f"'{file_path_for_excel}', "
            f"sheet='{sheet_name}', "
            f"empty_as_varchar=true"
            f")"
        )

        if query_spec is None:
            return f"SELECT *{from_clauses}"

        if isinstance(query_spec.select, list):
            valid_columns = DuckDBQueryBuilder._filtering_valid_select_columns(query_spec.select)

            if not valid_columns or "*" in valid_columns:
                select_clauses = "*"

            else:
                select_clauses = ', '.join(
                    DuckDBQueryBuilder._escape_identifier(col)
                    for col in valid_columns
                )
        else:
            select_clauses = DuckDBQueryBuilder._escape_identifier(
                validate_column_name(query_spec.select)
            ) or "*"

        select_clauses = f"SELECT {select_clauses}"

        full_clauses = select_clauses + from_clauses

        if query_spec.where:
            full_clauses += f" WHERE {query_spec.where.strip()}"

        if query_spec.group_by:
            full_clauses += f" GROUP BY {query_spec.group_by.strip()}"

        if query_spec.order_by:
            full_clauses += f" ORDER BY {query_spec.order_by.strip()}"

        return full_clauses

    @staticmethod
    def build_simple_join_query(
            left_view_name: str,
            right_view_name: str,
            join_keys: dict[str, str],
            how: Literal["LEFT", "RIGHT", "INNER", "FULL OUTER"],
    ) -> str:
        join_on_clause = " AND ".join(
            f"{left_view_name}.{left_column_name} = {right_view_name}.{right_column_name}"
            for left_column_name, right_column_name in join_keys.items()
        )

        return f"""
            SELECT *
            FROM {left_view_name}
            {how} JOIN {right_view_name}
            ON {join_on_clause}
        """

    @staticmethod
    def build_join_query(
            left_view_name: str,
            left_view_columns: list[str],
            right_view_name: str,
            right_view_columns: list[str],
            join_keys: dict[str, str],
            how: Literal["LEFT", "RIGHT", "INNER", "FULL OUTER"],
            drop_joined_view_common_cols: bool = False,
    ) -> Optional[str]:
        """
        두 컬럼 목록에 대한 join query 를 반환

        [WARN]
        해당 메서드는 일반적인 SQL 의 join 쿼리가 아닌 특정 컬럼명 규칙 (alias) 을 추가한 join 쿼리를 반환하므로,
        주의 사항을 반드시 참고 후 활용을 권고

        파라미터의 how 에 지정되지 않은 잘못된 값이 들어오거나,
        left/right_view_columns 양측 모두에 각각 매핑된 join_keys 의 key/value 원소 중 하나라도 존재하지 않을 경우
        검증 후 None 을 반환

        주의 사항
        - 컬럼 순서는 파라미터로 입력된 컬럼의 순서를 따름

        - join key 가 아닌 공통 컬럼명의 경우,
          기준이 되는 데이터 단위의 컬럼명은 그대로 사용,
          join 상대 측의 데이터 단위의 컬럼명은 {컬럼명}__{상대 측_view_name} 으로 변경됨
          (ex. left_view[id, a, b] LEFT JOIN right_view[id, a, c] ON [id] 라 가정하면,
               결과는 [id, a (left view), a__right_view, b, c] 가 됨)

        - FULL OUTER JOIN 의 경우, join keys 및 공통 컬럼은 각각 별도의 alias 가 추가된 개별 컬럼으로 출력됨
          (ex. REVIEW_ID__{left_view_name}, REVIEW_ID__{right_view_name})

        - drop_joined_view_common_cols 설정을 통해 join 기준 상대측의 join key 가 아닌 공통 컬럼을 SELECT 에서 제외할 수 있음
          (ex. left_view[id, a, b] LEFT JOIN right_view[id, a, c] ON [id] 라 가정하면,
               결과는 [id, a (left_view), b, c] 가 됨)

          단, INNER/FULL OUTER JOIN 의 경우 drop_joined_view_common_cols=True 라면 양측의 공통 컬럼이 모두 탈락되며,
          FULL OUTER JOIN 한정으로 join keys 에 해당하는 컬럼들은 drop 되지 않고 개별 alias 컬럼으로 출력됨

        - 해당 쿼리로 duck db 의 query() 에 활용할 경우,
          반드시 register() 에 등록한 alias (view_name) 문자열을 XXX_df_name 파라미터에 입력해야 함

        - 해당 쿼리는 단순 fstring 으로 작성되기에 SQL injection 에 취약할 수 있음
          주요 로직이 아닌, 내부적인 로직에서만 사용을 권고

        - preprocessing.py 단계를 거친 데이터는 id 정보가 문자열로 파싱되어 있으니,
          raw 한 데이터와 preprocessing 을 거친 데이터를 join 할 경우 논리적 오류를 방지하기 위해
          id 값은 str 타입으로 파싱한 후 join 쿼리를 적용할 것을 권고

        :param left_view_name: join query 상 왼쪽에 위치하는 데이터 단위의 alias
        :param left_view_columns: join query 상 왼쪽에 위치하는 데이터 단위의 컬럼 목록 list[str]
        :param right_view_name: join query 상 오른쪽에 위치하는 데이터 단위의 alias
        :param right_view_columns: join query 상 오른쪽에 위치하는 데이터 단위의 컬럼 목록 list[str]
        :param join_keys: join 의 대상이 되는 컬럼 매핑 정보 dict[str, str]
        :param how: join 방식을 정의하는 Literal["LEFT", "RIGHT", "INNER", "FULL OUTER"]
        :param drop_joined_view_common_cols: join 기준 상대측의 데이터 단위 중 join key 가 아닌, 공통 컬럼의 제거 여부
        :return: 조건에 맞는 join 쿼리 Optional[str]
        """

        # 검증 로직
        # join_keys 파라미터 검증
        def is_empty(columns):
            return columns is None or (isinstance(columns, Sized) and len(columns) == 0)

        if is_empty(join_keys) or is_empty(left_view_columns) or is_empty(right_view_columns):
            logging.warning("[SKIP] process=build_join_query, parameter=join_keys, left/right_view_columns: "
                            "Join keys and left/right view columns are must not be empty - return None")
            return None

        # left/right_view_columns 파라미터 검증 (중복 column 여부)
        if len(set(left_view_columns)) != len(left_view_columns):
            logging.warning("[WARN] process=build_join_query, parameter=left_view_columns: "
                            "Found duplicate column(s) in parameter")

        if len(set(right_view_columns)) != len(right_view_columns):
            logging.warning("[WARN] process=build_join_query, parameter=right_view_columns: "
                            "Found duplicate column(s) in parameter")

        left_view_columns = list(OrderedDict.fromkeys(left_view_columns))
        right_view_columns = list(OrderedDict.fromkeys(right_view_columns))

        left_view_set = set(left_view_columns)
        right_view_set = set(right_view_columns)
        left_join_keys = set(join_keys.keys())
        right_join_keys = set(join_keys.values())

        # left/right_cols 양쪽 모두가 join_keys 를 가지고 있는지 검증
        for left_key, right_key in join_keys.items():
            if left_key not in left_view_columns or right_key not in right_view_columns:
                logging.warning("[SKIP] process=build_join_query, parameter=join_keys: "
                                "Join keys must be in both column lists - return None")
                return None

        left_diff_cols = [
            c for c in left_view_columns
            if c not in right_view_set and c not in left_join_keys
        ]
        right_diff_cols = [
            c for c in right_view_columns
            if c not in left_view_set and c not in right_join_keys
        ]
        non_join_common_cols = [
            c for c in left_view_columns
            if c in right_view_set and c not in left_join_keys and c not in right_join_keys
        ]

        select_clauses = []
        if how == "LEFT":
            select_clauses.append(f"{left_view_name}.*")
            select_clauses.extend(
                f"{right_view_name}.{col}"
                for col in right_diff_cols
            )
            if not drop_joined_view_common_cols:
                select_clauses.extend(
                    f"{right_view_name}.{col} AS {col}__{right_view_name}"
                    for col in non_join_common_cols
                )

        elif how == "RIGHT":
            select_clauses.append(f"{right_view_name}.*")
            select_clauses.extend(
                f"{left_view_name}.{col}"
                for col in left_diff_cols
            )
            if not drop_joined_view_common_cols:
                select_clauses.extend(
                    f"{left_view_name}.{col} AS {col}__{left_view_name}"
                    for col in non_join_common_cols
                )

        elif how in ("INNER", "FULL OUTER"):

            if how == "INNER":
                select_clauses.append(f"{left_view_name}.*")
                select_clauses.extend(
                    f"{right_view_name}.{col}"
                    for col in right_diff_cols
                )

            else:   # how == "FULL OUTER"
                select_clauses.extend(
                    f"{left_view_name}.{col}"
                    for col in left_diff_cols
                )
                select_clauses.extend(
                    f"{right_view_name}.{col}"
                    for col in right_diff_cols
                )

                for left_key, right_key in join_keys.items():
                    select_clauses.append(f"{left_view_name}.{left_key} AS {left_key}__{left_view_name}")
                    select_clauses.append(f"{right_view_name}.{right_key} AS {right_key}__{right_view_name}")

            if not drop_joined_view_common_cols:
                select_clauses.extend(
                    f"{left_view_name}.{col} AS {col}__{left_view_name}"
                    for col in non_join_common_cols
                )
                select_clauses.extend(
                    f"{right_view_name}.{col} AS {col}__{right_view_name}"
                    for col in non_join_common_cols
                )

        else:
            logging.warning("[SKIP] process=build_join_query, parameter=how: Invalid value in parameter - return None")
            return None

        select_clause = '\n, '.join(select_clauses)

        on_clause = " AND ".join(
            f"{left_view_name}.{left_key} = {right_view_name}.{right_key}"
            for left_key, right_key in join_keys.items()
        )

        return f"""
            SELECT 
                {select_clause}
            FROM 
                {left_view_name}
                {how} JOIN {right_view_name}
                ON {on_clause}
        """

    @staticmethod
    def build_create_temp_view_query(
            output_view_name: str,
            query: str,
    ) -> str:
        """
        쿼리 적용 후 output view name 의 view 에 저장하는 쿼리문 반환

        :param output_view_name: 쿼리 적용 후 저장할 view name str
        :param query: 적용 대상 쿼리문 str
        :return: 쿼리 적용 후 output view name 의 view 에 저장하는 전체 쿼리문 str
        """

        return f"""
            CREATE OR REPLACE TEMP VIEW {output_view_name}
            AS {query}
        """

    @staticmethod
    def build_select_all_query(
            view_name: str,
    ) -> str:
        """
        view name 에 해당하는 view 로부터 전체 데이터를 반환하는 쿼리문 반환

        :param view_name: 대상 view name str
        :return: SELECT * FROM view_name 에 해당하는 쿼리문 str
        """

        return f"""
            SELECT *
            FROM {view_name}
        """
