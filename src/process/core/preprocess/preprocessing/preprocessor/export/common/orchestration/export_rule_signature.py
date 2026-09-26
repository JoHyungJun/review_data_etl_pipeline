"""
export_rule_signature.py
------------------------

export 포맷 기준, 스크래핑 대상 플랫폼마다 다르게 적용되어야 할 추가적인 데이터 전처리 메서드의 시그니처를 정의한 모듈

해당 포맷은 구조적 타이핑 형식으로 EXPORT_RULE_MAPPING 의 메서드 포맷 규칙에 적용됨

주의 사항
- 해당 구조의 메서드들은 다음과 같은 형식을 지켜야 함
    - 파라미터 : (pandas.DataFrame (export format 처리 된 df), SourceDataContext)
    - return 타입 : pandas.DataFrame
"""


from typing import Protocol

import pandas as pd

from process.core.preprocess.preprocessing.model.context.source_data_context import SourceDataContext


class ExportRuleSignature(Protocol):

    def __call__(
            self,
            export_formatted_df: pd.DataFrame,
            source_data_context: SourceDataContext,
    ) -> pd.DataFrame:
        pass
