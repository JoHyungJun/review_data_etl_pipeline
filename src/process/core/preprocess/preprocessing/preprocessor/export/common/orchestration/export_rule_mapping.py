"""
export_rule_mapping.py
----------------------

export 포맷 기준, 스크래핑 대상 플랫폼마다 다르게 적용되어야 할 추가적인 데이터 전처리 작업의 조합을 관리하는 모듈

해당 모듈은 {tuple(리뷰 수집 대상 플랫폼, export 대상) : 처리 대상 메서드} 매핑 정보만을 관리하며,
로직은 export_rule_applier() 메서드를 통해 적용해야 함
"""


from domain.platform.platform import Platform
from process.core.preprocess.preprocessing.preprocessor.export.common.orchestration.export_rule_signature import \
    ExportRuleSignature
from process.core.preprocess.preprocessing.preprocessor.export.vreview.rules.ably_rule import ably_to_vreview_preprocessing
from process.core.preprocess.preprocessing.preprocessor.export.vreview.rules.coupang_rule import \
    coupang_to_vreview_preprocessing


EXPORT_RULE_MAPPING: dict[tuple[Platform, Platform], ExportRuleSignature] = {
    (Platform.ABLY, Platform.VREVIEW): ably_to_vreview_preprocessing,
    (Platform.COUPANG, Platform.VREVIEW): coupang_to_vreview_preprocessing,
}
