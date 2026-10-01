"""
ini_config_adapter.py
---------------------

ini 형태의 외부 설정값 파일로부터 데이터를 추출하여
dict[str, Section] 구조로 반환하는 클래스 모듈
"""


import configparser
from pathlib import Path
from typing import Union, Optional

from core.base.adapter.base_section_based_config_adapter import BaseSectionBasedConfigAdapter
from core.config.model.config_base_section_option import Section, Option
from util.logging_util import logging_error_event


class IniConfigAdapter(BaseSectionBasedConfigAdapter):

    @classmethod
    def _load_ini_config_to_dict(cls, ini_path: Union[Path, str]) -> Optional[dict]:
        """
        INI 파일 load 및 파싱 후 dict 형태로 반환

        해당 메서드는 외부 설정값 ini config dict 생성에도 사용되므로
        엄격한 분기 처리 (예외 시 None 반환 없이 무조건 에러 반환)

        :param ini_path: INI 파일 경로
        :return: INI 파일 존재 여부에 따른 load 및 파싱된 INI 데이터 Optional[dict]
        """

        try:
            parser = configparser.ConfigParser(interpolation=None)
            parser.read(Path(ini_path), encoding="utf-8")
            return {
                section: dict(parser[section]) for section in parser.sections()
            }
        except FileNotFoundError as e:
            logging_error_event(
                log_prefix="LOAD",
                log_metadata={
                    "file_path": ini_path,
                },
                log_message="Not found INI configuration file",
                log_message_detail=str(e),
            )
            raise
        except configparser.MissingSectionHeaderError as e:
            logging_error_event(
                log_prefix="PARSE",
                log_metadata={
                    "file_path": ini_path,
                },
                log_message="Parsing error detected in the INI file",
                log_message_detail=str(e),
            )
            raise RuntimeError(f"INI 파일에서 구문 오류를 발견했습니다.:\n{e}")
        except Exception as e:  # pylint: disable=broad-except
            logging_error_event(
                log_prefix="LOAD",
                log_metadata={
                    "file_path": ini_path,
                },
                log_message="While loading INI file",
                log_message_detail=str(e),
            )
            raise

    @classmethod
    def _parse_ini_dict_to_schema_format(cls, ini_dict: dict) -> dict[str, Section]:
        """
        INI dict 데이터를 Section-based configuration (Section/Option) 구조 dict 로 변환 및 반환

        :param ini_dict: INI dict
        :return: 파싱된 Section-based configuration 구조의 dict
        """

        schema: dict[str, Section] = {}

        for section_name, options_dict in ini_dict.items():
            section = Section(section_name)

            for option_key, option_value in options_dict.items():
                # INI 는 외부 설정 파일로, meta 정보 작성 불가 (스키마에 정의되지 않은 외부값은 meta=None)
                option = Option(
                    key=option_key,
                    value=option_value if option_value != '' else None,
                    meta=None,
                )
                section.add_option(option)

            schema[section_name] = section

        return schema

    @classmethod
    def load_to_section_based_dict(cls, file_path: Union[Path, str]) -> dict[str, Section]:
        """
        ini 포맷으로 저장되어 있는 외부 파일에 작성된 설정값 load 및
        Section-based 구조의 dict 으로 반환

        ini 외부 파일은 반드시 해당 메서드의 파싱 로직 포맷대로 작성되어야 함

        :param file_path: 파싱 대상 ini 외부 설정 파일 경로 Union[Path, str]
        :return: 파싱된 Section 명이 key 가 되는 dict[str, Section]
        """

        file_path = Path(file_path)

        ini_dict = cls._load_ini_config_to_dict(file_path)
        return cls._parse_ini_dict_to_schema_format(ini_dict)
