"""
batch_snapshot.py
-----------------

batch 기반 감성 추론 로직 수행 중, 특정 시점에서의 batch 내부 정보 및 상태 정보 관리 클래스 모듈
"""


from __future__ import annotations
from dataclasses import dataclass


@dataclass(slots=True)
class TextTokenLengthMapping:
    """
    개별 text 의 길이와,
    해당 text 가 tokenizer 에 의해 token 으로 나눠졌을 때의 길이 정보 관리 클래스
    """
    
    text_length: int
    token_length: int


@dataclass(slots=True, frozen=True)
class BatchSnapshotSummary:
    """
    개별 batch 내부 정보 및 상태 정보 관리 클래스

    batch 내부에 들어 있는 개별 원소들의 raw text/token length 정보를 기반으로
    연산된 주요 summary 정보들을 관리 및 제공

    주의 사항
    - raw 데이터와 summary 의 정합성을 위해,
      해당 클래스의 생성자를 통한 직접적인 인스턴스화 보다
      내부 팩토리 메서드를 활용하길 권고
    """

    # batch
    batch_size: int

    # token
    max_token_count_per_batch: int
    total_token_count_per_batch: int

    @classmethod
    def from_text_token_length_mappings(
            cls,
            text_token_length_mappings: list[TextTokenLengthMapping],
    ) -> BatchSnapshotSummary:
        batch_size = len(text_token_length_mappings)

        token_lengths = [mapping.token_length for mapping in text_token_length_mappings]

        return cls(
            batch_size=batch_size,

            max_token_count_per_batch=max(token_lengths) if token_lengths else 0,
            total_token_count_per_batch=sum(token_lengths),
        )


@dataclass(slots=True)
class BatchSnapshot:
    """
    개별 batch 내부 정보 및 상태 정보와 raw 데이터 관리 클래스

    batch 내부에 들어 있는 개별 원소들의 text/token length 정보에 대한 raw 데이터를 관리하며,
    해당 정보를 기준으로 연산된 summary 정보를 제공

    주의 사항
    - raw 데이터와 summary 의 정합성을 위해,
      해당 클래스의 생성자를 통한 직접적인 인스턴스화 보다
      내부 팩토리 메서드를 활용하길 권고
    """

    # summary
    batch_snapshot_summary: BatchSnapshotSummary

    # raw data
    text_token_length_mappings: list[TextTokenLengthMapping]

    @classmethod
    def from_text_token_length_mappings(
            cls,
            text_token_length_mappings: list[TextTokenLengthMapping],
    ) -> BatchSnapshot:

        return cls(
            batch_snapshot_summary=BatchSnapshotSummary.from_text_token_length_mappings(
                text_token_length_mappings=text_token_length_mappings,
            ),
            text_token_length_mappings=text_token_length_mappings,
        )
