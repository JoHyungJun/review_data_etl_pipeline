"""
base_config_adapter.py
----------------------

외부 파일에 작성된 설정값 파싱을 위한 추상 클래스 모듈

외부 설정 파일 (INI, Excel 등) 로부터 설정 데이터를 load 하여
프로젝트 설정값 관리 표준 구조 (Dict[str, Section]) 로 변환하기 위한 추상화 인터페이스를 제공

주의 사항
- 해당 프로젝트는 비즈니스 로직에 직접 영향을 끼치는, 외부 파일에서 명시되는 설정값에 대해
  Section-based dict 구조 (str: Section: Option - OptionValue) 를 사용하고 있으며,

  따라서 외부 파일에 접근하여 설정값을 가져오는 클래스는
  반드시 해당 클래스를 상속받고 규격에 맞게 dict 를 반환하여 ConfigRegistry 를 구성해야 함
"""


from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict

from core.config.model.config_base_section_option import Section


class BaseConfigAdapter(ABC):

    @classmethod
    @abstractmethod
    def load_to_section_based_dict(cls, file_path: Path) -> Dict[str, Section]:
        """
        외부 파일에 작성된 설정값 load 및
        Section-based 구조의 dict 으로 반환
        
        해당 메서드는
        config 파일 포맷별 데이터 load + Section-based 구조의 dict 를 반환하는 책임을 가지며,
        이는 ConfigRegistry 에서 활용됨

        :param file_path: 파싱 대상 외부 설정 파일 경로
        :return: 파싱된 Section 명이 key 가 되는 Dict[str, Section]
        """
        pass
