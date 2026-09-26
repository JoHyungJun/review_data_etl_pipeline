"""
log_util.py
-----------

감성 추론 관련 util 모듈
"""


from collections import defaultdict

from process.core.postprocess.postprocessing.postprocessor.common.sentiment.log.model.models import BaseSentimentLog
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.type.event_types import \
    SentimentLogEventType


def group_sentiment_logs_by_event_type(
        sentiment_logs: list[BaseSentimentLog]
) -> dict[SentimentLogEventType, list]:
    """
    BaseSentimentLog 객체 list 를 event_type 에 따라 그룹핑 및 반환

    :param sentiment_logs: BaseSentimentLog 혹은 자식 객체들의 list[BaseSentimentLog]
    :return: event_type 에 따라 그룹핑 된 dict[SentimentLogEventType, list]:
    """

    grouped_dict = defaultdict(list)
    for log in sentiment_logs:
        grouped_dict[log.event_type].append(log)

    return dict(grouped_dict)
