"""
btree.py
--------

BTree 자료구조 및 데이터 추출 관련 util 모듈

대용량의 데이터에 대한 관리 및 추출에 활용
"""


import logging
from pathlib import Path
from typing import Union, Optional, Any
import pandas as pd


class BTreeNode:
    """
    Btree 의 개별 노드 단위 데이터 관리 클래스
    """

    def __init__(self, is_leaf: bool = False):
        self.is_leaf = is_leaf
        self.keys = []
        self.children = []


class BTreeIndex:
    """
    BTree 의 탐색, 삽입 등 데이터 전반을 관리하는 key-value 구조의 인덱스 클래스

    - 삽입, 검색, bulk load 등의 데이터 관리 기능 제공
    - 데이터 개별 노드 단위로 BTreeNode 를 사용
    """

    def __init__(self, degree: int = 128):
        self.root = BTreeNode(is_leaf=True)
        self.degree = degree

    def search(self, key: Any) -> Optional[Any]:
        """
        BTree 에서 key 로 노드 탐색

        :param key: 탐색 대상 key
        :return: key 에 대응하는 Optional value
        """

        x = self.root
        while True:
            i = 0

            while i < len(x.keys) and key > x.keys[i][0]:
                i += 1

            if i < len(x.keys) and key == x.keys[i][0]:
                return x.keys[i][1]

            if x.is_leaf:
                return None

            x = x.children[i]

    def insert(self, key: Any, value: Any) -> None:
        """
        BTree 에 key 와 해당 key 에 대응하는 데이터 value 삽입

        루트 노드가 가득 찼다면 새로운 루트 노드 생성 후 분할
        루트 노드가 가득 차지 않았다면 루트부터 재귀 탐색하여 공간이 있는 노드에 삽입

        :param key: 삽입 대상 key
        :param value: 삽입 대상 value
        """

        root = self.root
        
        # 루트 노드가 가득 찼다면 루트 분할 후 삽입
        if len(root.keys) == (2 * self.degree) - 1:
            new_root = BTreeNode()
            self.root = new_root
            new_root.children.insert(0, root)

            self._split_child(new_root, 0)
            self._insert_to_non_full_node(new_root, key, value)
        
        # 루트 노드가 가득 차지 않았다면 재귀 탐색 후 공간이 있는 노드에 삽입
        else:
            self._insert_to_non_full_node(root, key, value)

    def _insert_to_non_full_node(self, node: BTreeNode, key: Any, value: Any) -> None:
        """
        공간이 있는 노드에 key 와 해당 key 에 대응하는 데이터 value 삽입

        :param node: 삽입 대상 node
        :param key: 삽입 대상 key
        :param value: 삽입 대상 value
        :return: 없음
        """

        idx = len(node.keys) - 1
        
        # 해당 노드가 leaf 노드라면 삽입 후 정렬
        if node.is_leaf:
            node.keys.append((key, value))
            node.keys.sort(key=lambda item: item[0])

        # 해당 노드가 leaf 노드가 아니라면 재귀 탐색 후 삽입
        else:
            # 현재 key 보다 작은 key 의 인덱스를 찾기 위해 역방향 탐색
            while idx >= 0 and key < node.keys[idx][0]:
                idx -= 1
            idx += 1
            # 자식 노드가 가득 찼다면 분할
            if len(node.children[idx].keys) == (2 * self.degree) - 1:
                self._split_child(node, idx)
                
                # 분할 후, 새로 생성된 노드 쪽으로 이동 필요 여부 판단
                if key > node.keys[idx][0]:
                    idx += 1

            # 적절한 자식 노드로 재귀 삽입
            self._insert_to_non_full_node(node.children[idx], key, value)

    def _split_child(self, parent_node: BTreeNode, child_idx: int) -> None:
        """
        parent_node 의 자식 노드 (child_idx) 가 가득 찼을 때 분할 처리

        - 자식 노드가 (2 * degree - 1) 개의 key 를 모두 채웠다면,
          자식 노드 (child_node) 를 두 개로 나누고, 중간 key 를 parent_node 로 이동
        - 해당 노드의 leaf 여부 (is_leaf) 를 유지하면서 자식 key 들 (children) 을 나누어 재배치

        :param parent_node: 분할 대상 자식이 속한 부모 노드
        :param child_idx: 분할 대상 자식 노드 인덱스
        :return: 없음
        """

        degree = self.degree

        child_node = parent_node.children[child_idx]
        new_sibling = BTreeNode(is_leaf=child_node.is_leaf)

        # 형제 노드 삽입 (parent_node 에 삽입)
        parent_node.children.insert(child_idx + 1, new_sibling)

        # 중간 key 를 parent_node 로 이동
        parent_node.keys.insert(child_idx, child_node.keys[degree - 1])
        
        # 기존 child_node 의 key 절반을 형제 노드 (new_sibling) 로 이동
        new_sibling.keys = child_node.keys[degree:(2 * degree) - 1]
        child_node.keys = child_node.keys[0:degree - 1]
        
        # internal node 라면 children 도 절반 분할하여 이동
        if not child_node.is_leaf:
            new_sibling.children = child_node.children[degree:(2 * degree)]
            child_node.children = child_node.children[0:degree]

    def values(self) -> list[Any]:
        """
        BTree 전체 노드들의 전체 value 를 추출하여 반환

        :return: BTree 에 저장된 모든 value 리스트
        """

        result = []
        self._collect_values(self.root, result)

        return result

    def _collect_values(self, node: BTreeNode, result: list[Any]) -> None:
        """
        현재 노드의 value 추가 및 자식 노드로 재귀 수행

        :param node: 탐색 대상 노드
        :param result: value 수집용 리스트
        :return: 없음
        """

        # 현재 노드가 leaf 라면 value 수집
        if node.is_leaf:
            result.extend([value for _, value in node.keys])

        # 현재 노드가 internal 노드라면 value 수집 후 자식 노드로 재귀 수행
        else:
            for i in range(len(node.keys)):
                self._collect_values(node.children[i], result)
                result.append(node.keys[i][1])

            self._collect_values(node.children[-1], result)

    def bulk_load(self, items: list[tuple[Any, Any]]) -> None:
        """
        여러 삽입 대상 key 및 해당 key 에 대응하는 value 쌍을 정렬 후 BTree 에 순차 삽입

        :param items: 삽입 대상 (key, value) List[tuple[Any, Any]]
        :return: 없음
        """

        # key 기준 오름차순 정렬
        items.sort(key=lambda x: x[0])
        
        # 정렬 순으로 순차 삽입
        for key, value in items:
            self.insert(key, value)


def build_btree_from_excel(
        file_path: Union[Path, str],
        pk_column_name: str,
        reversed_column_map: Optional[dict] = None,
) -> BTreeIndex:
    """
    Excel 에서 전체 데이터를 읽고 BTree 자료구조 (BTreeIndex) 로 변환

    - 기존 데이터가 저장되어 있는 Excel 을 읽고, 해당 DataFrame 을 dict list 인 record 로 변환하여 bulk load
    - 추가 삽입되는 API response 의 json 데이터들과 포맷 및 key 명을 일치시키기 위해,
      기존 Excel 에서 바뀌어 저장된 컬럼명을 다시 API response 의 동일 key 명으로 역변환

    :param file_path: Excel 경로 Union[Path, str]
    :param pk_column_name: key 로 사용할 컬럼명 (primary) str
    :param reversed_column_map: {컬럼명 : json key} 로 역변환된 Optional[dict]
    :return: 변환 및 초기화된 BTreeIndex 인스턴스 BTreeIndex
    """

    btree = BTreeIndex(degree=128)

    try:
        df = pd.read_excel(file_path, engine='openpyxl')
    except FileNotFoundError:
        logging.warning(f"[LOAD] file_path:{file_path}: No file in this path")
        return btree

    # Excel 컬럼명을 기존 json key 명으로 역변환하여 관리
    if reversed_column_map:
        df.rename(columns=reversed_column_map, inplace=True)

    # DataFrame 을 List[dict] 형태로 변환
    records = df.to_dict(orient="records")

    items = [(str(rec[pk_column_name]), rec) for rec in records]
    btree.bulk_load(items)

    return btree
