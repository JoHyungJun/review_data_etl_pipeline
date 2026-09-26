"""
export_data_context.py
----------------------

preprocessing 에서 수집된 데이터 및 컬럼명으로 활용되는 export schema 정의 모듈

파이프라인의 규칙에 의해 특정 attribute schema 는 None 이 될 수 있으며,
이에 대한 validate 및 처리에 대한 책임은 개별 호출부가 가짐

해당 클래스가 관리하는 개별 값에에 대한 정보는 다음과 같음

- export_formatted_df:
    export schema 에 선언된 컬럼명 정보 기반 데이터를 가지고 있는 pandas.DataFrame

- export_attribute_schema:
    export 별 컬럼명 정보 관련 Type[BaseExportAttributeSchema]
"""


from typing import Type, Optional

import pandas
from dataclasses import dataclass

from core.base.schema.attribute.base_export_attribute_schema import \
    BaseExportAttributeSchema


@dataclass(frozen=True)
class ExportDataContext:

    export_formatted_df: pandas.DataFrame

    export_attribute_schema: Optional[Type[BaseExportAttributeSchema]]

    def unpack(self):
        """
        해당 클래스가 관리하는 모든 변수를 하나의 tuple 로 반환

        :return: 해당 클래스가 관리하는 모든 변수를 가진
                 tuple[
                    export_attribute_schema,
                    export_formatted_df
                 ]
        """

        return (
            self.export_attribute_schema,
            self.export_formatted_df,
        )
