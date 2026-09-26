"""
export_rule_applier.py
----------------------

export 포맷 기준, 스크래핑 대상 플랫폼마다 다르게 적용되어야 할 추가적인 데이터 전처리 로직을 적용하는
공통 메서드를 관리하는 모듈

해당 모듈은 EXPORT_RULE_MAPPING 매핑 정보를 통해
{export: 리뷰 플랫폼} 조합에 해당되는 전처리 메서드를 적용하고 결과 df 를 반환
"""


import logging

import pandas as pd

from domain.platform.platform import Platform
from process.core.preprocess.preprocessing.model.context.source_data_context import SourceDataContext
from process.core.preprocess.preprocessing.preprocessor.export.common.orchestration.export_rule_mapping import EXPORT_RULE_MAPPING


def export_rule_applier(
        export_formatted_df: pd.DataFrame,
        source_data_context: SourceDataContext,
        export_platform: Platform,
        target_platform: Platform,
) -> pd.DataFrame:
    rule_key = (target_platform, export_platform)
    target_to_export_preprocessor = EXPORT_RULE_MAPPING.get(rule_key)

    if target_to_export_preprocessor is None:
        logging.debug(
            f"[FORMAT] process=export_rule_applier, "
            f"export_platform={export_platform}, target_platform={target_platform}: "
            f"Not found preprocessor in export rule mapping"
        )
        return export_formatted_df

    return target_to_export_preprocessor(export_formatted_df, source_data_context)
