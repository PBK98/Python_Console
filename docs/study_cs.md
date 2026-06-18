# CS Study Notes for Budget App

이 문서는 파일 기반 가계부 콘솔 프로그램 과제를 수행하기 전에 알아두면 좋은 CS 개념을 정리한 학습 노트입니다.

과제의 핵심은 단순히 Python 문법으로 기능을 만드는 것이 아니라, 데이터를 안전하게 저장하고, 유지보수 가능한 구조로 작은 서비스를 설계하는 것입니다.

## 1. 파일 기반 데이터 저장

이 과제는 데이터베이스를 사용하지 않고 파일에 데이터를 저장합니다. 프로그램을 종료해도 거래 내역, 카테고리, 예산 정보가 남아 있어야 하므로 파일 기반 영구 저장을 이해해야 합니다.

알아야 할 내용:

- 파일 열기, 읽기, 쓰기, 추가하기
- UTF-8 인코딩
- CSV 또는 JSONL 저장 형식
- 저장 파일을 역할별로 분리하는 이유
- 프로그램 실행 시 파일이 없을 때 초기화하는 방법

예상 저장 파일:

```text
data/
  transactions.jsonl
  categories.jsonl
  budgets.jsonl
```

또는:

```text
data/
  transactions.csv
  categories.csv
  budgets.csv
```

파일을 여러 개로 나누는 이유는 데이터의 책임이 다르기 때문입니다. 거래 내역, 카테고리, 예산은 서로 관련은 있지만 같은 데이터는 아니므로 분리해서 관리하는 편이 유지보수에 좋습니다.

## 2. CSV와 JSONL

이 과제에서는 CSV 또는 JSONL 중 하나를 선택할 수 있습니다.

CSV는 표 형태 데이터에 적합합니다.

```csv
date,type,category,amount,memo,tags
2024-01-15,expense,food,15000,점심,meal
```

장점:

- 사람이 읽기 쉽습니다.
- 스프레드시트 프로그램에서 열기 쉽습니다.
- import/export 기능과 잘 맞습니다.

단점:

- 리스트나 중첩 구조를 표현하기 어렵습니다.
- 쉼표, 줄바꿈, 따옴표 처리를 조심해야 합니다.

JSONL은 한 줄에 JSON 객체 하나를 저장하는 방식입니다.

```json
{"id": "TX-000001", "date": "2024-01-15", "type": "expense", "category": "food", "amount": 15000, "memo": "점심", "tags": ["meal"]}
```

장점:

- Python dict와 잘 맞습니다.
- tags 같은 리스트를 자연스럽게 저장할 수 있습니다.
- 한 줄씩 읽기 좋아서 스트리밍 처리에 적합합니다.

단점:

- 일반 사용자가 직접 수정하기에는 CSV보다 낯설 수 있습니다.

이 과제에서는 `tags`처럼 리스트 데이터가 있으므로 JSONL을 선택하면 구현이 조금 더 자연스럽습니다. 다만 import/export는 요구사항상 CSV 스키마를 맞춰야 합니다.

## 3. CRUD

CRUD는 대부분의 서비스가 제공하는 기본 데이터 조작 방식입니다.

| 개념 | 의미 | 과제 기능 |
| --- | --- | --- |
| Create | 데이터 생성 | `add`, `import` |
| Read | 데이터 조회 | `list`, `search`, `summary`, `export` |
| Update | 데이터 수정 | `update`, `budget set`, `category add/remove` |
| Delete | 데이터 삭제 | `delete`, `category remove` |

가계부 프로그램도 결국 거래 데이터를 만들고, 조회하고, 수정하고, 삭제하는 CRUD 프로그램입니다.

## 4. 데이터 모델링

데이터 모델링은 프로그램에서 다룰 데이터가 어떤 필드를 가져야 하는지 정하는 작업입니다.

거래 내역은 최소한 아래 필드를 가져야 합니다.

```text
id
date
type
category
amount
memo
tags
```

Python에서는 `dataclass`를 사용하면 데이터 구조를 명확하게 표현할 수 있습니다.

```python
from dataclasses import dataclass


@dataclass
class Transaction:
    id: str
    date: str
    type: str
    category: str
    amount: int
    memo: str = ""
    tags: list[str] | None = None
```

데이터 모델을 명확히 만들면 함수들이 어떤 데이터를 주고받는지 이해하기 쉬워지고, 나중에 기능을 추가할 때 실수를 줄일 수 있습니다.

## 5. 타입 힌트

타입 힌트는 함수의 입력과 출력 계약을 코드에 적어두는 방식입니다.

```python
def find_transaction(transaction_id: str) -> Transaction | None:
    ...
```

이 함수는 문자열 id를 받아서 `Transaction`을 반환하거나, 찾지 못하면 `None`을 반환한다는 뜻입니다.

타입 힌트의 장점:

- 함수의 의도를 쉽게 알 수 있습니다.
- 잘못된 타입의 값을 넘기는 실수를 줄일 수 있습니다.
- 코드 자동완성과 정적 분석에 도움이 됩니다.
- 협업하거나 나중에 다시 볼 때 이해하기 쉽습니다.

이 과제에서는 모델, 저장소, 서비스 함수에 타입 힌트를 적극적으로 붙이는 것이 좋습니다.

## 6. 모듈화와 책임 분리

모듈화는 코드를 역할별 파일로 나누는 것입니다. 모든 코드를 한 파일에 넣으면 처음에는 편해 보이지만, 기능이 늘어날수록 수정하기 어려워집니다.

권장 구조:

```text
budget_app/
  __main__.py
  cli.py
  models.py
  repositories.py
  services.py
  validators.py
  decorators.py
```

각 모듈의 책임:

| 모듈 | 책임 |
| --- | --- |
| `__main__.py` | `python3 -m budget_app` 실행 진입점 |
| `cli.py` | 명령어와 옵션 처리 |
| `models.py` | 데이터 구조 정의 |
| `repositories.py` | 파일 읽기/쓰기 |
| `services.py` | 거래 추가, 검색, 요약 같은 핵심 로직 |
| `validators.py` | 날짜, 금액, 타입, 카테고리 검증 |
| `decorators.py` | 예외 처리, 로그, 실행 시간 측정 |

중요한 흐름은 다음과 같습니다.

```text
CLI -> Service -> Repository -> File
```

CLI는 사용자의 명령을 해석하고, Service는 실제 기능을 수행하며, Repository는 파일 입출력을 담당합니다.

## 7. 제너레이터와 스트리밍 처리

제너레이터는 `yield`를 사용해 값을 하나씩 꺼내는 함수입니다.

```python
def iter_transactions(path: str):
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            yield line
```

일반 함수는 결과를 한 번에 반환하지만, 제너레이터는 필요한 순간마다 하나씩 값을 반환합니다.

이 과제에서 제너레이터가 중요한 이유:

- 거래 파일 전체를 한 번에 메모리에 올리지 않아도 됩니다.
- 데이터가 많아져도 메모리 사용량이 안정적입니다.
- `list`, `search`, `summary` 같은 기능을 한 줄씩 처리할 수 있습니다.

예를 들어 거래가 10만 건이어도 파일을 한 줄씩 읽으면서 조건에 맞는 거래만 처리할 수 있습니다.

## 8. 검색과 필터링

검색은 여러 조건을 조합해서 원하는 데이터만 골라내는 작업입니다.

이 과제의 검색 조건:

- 기간: `--from`, `--to`
- 카테고리: `--category`
- 타입: `--type`
- 메모 키워드: `--q`
- 태그: `--tag`

필터링 함수는 보통 이런 형태가 됩니다.

```python
def matches(transaction: Transaction, criteria: SearchCriteria) -> bool:
    if criteria.category and transaction.category != criteria.category:
        return False
    if criteria.type and transaction.type != criteria.type:
        return False
    return True
```

조건이 많아질수록 코드를 읽기 쉽게 나누는 것이 중요합니다.

## 9. 집계와 요약

`summary` 기능은 단순 조회가 아니라 데이터를 계산해서 의미 있는 정보로 바꾸는 기능입니다.

필요한 계산:

- 총수입
- 총지출
- 잔액
- 카테고리별 지출 합계
- 지출 TOP N
- 예산 사용률
- 예산 초과 여부

카테고리별 합계는 딕셔너리로 계산할 수 있습니다.

```python
category_totals: dict[str, int] = {}

for transaction in transactions:
    if transaction.type == "expense":
        category_totals[transaction.category] = (
            category_totals.get(transaction.category, 0) + transaction.amount
        )
```

TOP N은 합계를 기준으로 정렬한 뒤 앞에서 N개만 가져오면 됩니다.

## 10. CLI와 argparse

CLI는 Command Line Interface의 약자로, 터미널에서 명령어로 사용하는 프로그램을 뜻합니다.

이 과제의 실행 예:

```bash
python3 -m budget_app add
python3 -m budget_app list --limit 3
python3 -m budget_app summary --month 2024-01 --top 3
python3 -m budget_app delete --id TX-000001
```

표준 라이브러리만 사용할 수 있으므로 `argparse`를 사용하는 것이 좋습니다.

`argparse`로 처리해야 할 것:

- subcommand: `add`, `list`, `search`, `summary`
- option: `--limit`, `--month`, `--from`, `--to`
- `--help` 출력
- 잘못된 명령어 처리

CLI는 사용자의 입력을 받는 영역이고, 실제 비즈니스 로직은 Service 계층으로 넘기는 구조가 좋습니다.

## 11. 입력 검증

입력 검증은 잘못된 데이터가 저장되지 않도록 막는 과정입니다.

검증해야 할 것:

- 날짜가 `YYYY-MM-DD` 형식인지
- 금액이 양수인지
- 타입이 `income` 또는 `expense`인지
- 카테고리가 등록되어 있는지
- 월 입력이 `YYYY-MM` 형식인지
- id가 실제로 존재하는지

입력 검증이 약하면 저장 파일에 잘못된 데이터가 들어가고, 이후 검색이나 요약 기능까지 함께 망가질 수 있습니다.

## 12. 예외 처리와 종료 코드

프로그램에서 오류가 발생했을 때 Python 스택트레이스를 그대로 보여주면 사용자가 이해하기 어렵습니다.

좋은 오류 메시지 예:

```text
[오류] 날짜 형식이 올바르지 않습니다.
[힌트] 예: 2024-01-15
```

알아야 할 내용:

- `try/except`
- 사용자 정의 예외
- `sys.exit(0)`과 `sys.exit(1)`
- 정상 종료와 비정상 종료의 차이

종료 코드:

| 코드 | 의미 |
| --- | --- |
| `0` | 정상 종료 |
| `0`이 아닌 값 | 오류 종료 |

## 13. 데코레이터

데코레이터는 함수를 감싸서 공통 기능을 추가하는 문법입니다.

예를 들어 여러 명령어에서 공통으로 예외 처리를 해야 한다면, 각 함수마다 `try/except`를 반복하기보다 데코레이터로 분리할 수 있습니다.

```python
from functools import wraps


def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as error:
            print(f"[오류] {error}")
            return 1

    return wrapper
```

사용 예:

```python
@handle_errors
def run_add_command(args) -> int:
    ...
```

데코레이터로 분리하기 좋은 공통 관심사:

- 예외 처리
- 실행 로그
- 실행 시간 측정

## 14. 데이터 무결성

데이터 무결성은 저장된 데이터가 일관되고 올바른 상태를 유지하는 것을 뜻합니다.

이 과제에서 중요한 무결성 규칙:

- 거래 id는 유일해야 합니다.
- 금액은 항상 양수여야 합니다.
- 거래 타입은 `income` 또는 `expense`만 허용해야 합니다.
- 등록되지 않은 카테고리로 거래를 추가하면 안 됩니다.
- 사용 중인 카테고리는 그냥 삭제하면 안 됩니다.
- 예산은 월 단위로 저장되어야 합니다.

무결성을 지키지 않으면 프로그램은 실행되더라도 결과가 틀릴 수 있습니다. 예를 들어 삭제된 카테고리를 사용하는 거래가 남아 있으면 summary에서 카테고리 집계가 애매해집니다.

## 15. update/delete와 파일 안전성

파일 기반 저장에서 수정과 삭제는 특히 조심해야 합니다.

기존 파일 중간의 한 줄만 안전하게 고치는 것은 쉽지 않습니다. 그래서 보통 아래 방식으로 처리합니다.

```text
1. 기존 파일을 한 줄씩 읽는다.
2. 수정 또는 삭제 결과를 임시 파일에 쓴다.
3. 모든 쓰기가 성공하면 임시 파일을 원래 파일로 교체한다.
```

이 방식의 장점:

- 중간에 오류가 나도 원본 파일이 남아 있습니다.
- 파일이 반쯤만 저장되는 문제를 줄일 수 있습니다.
- update/delete의 안정성이 좋아집니다.

Python에서는 `tempfile`과 `os.replace()`를 사용할 수 있습니다.

## 16. import/export

import는 외부 CSV 파일의 거래 데이터를 프로그램 저장소에 추가하는 기능입니다.

export는 저장된 거래 데이터를 조건에 맞게 CSV 파일로 내보내는 기능입니다.

CSV 최소 스키마:

| column | required | 설명 |
| --- | --- | --- |
| `date` | Y | `YYYY-MM-DD` |
| `type` | Y | `income` 또는 `expense` |
| `category` | Y | 등록된 카테고리 |
| `amount` | Y | 양수 정수 |
| `memo` | N | 문자열 |
| `tags` | N | 쉼표로 구분한 문자열 |

import에서 조심할 점:

- 헤더가 있는지 확인합니다.
- 필수 컬럼이 있는지 확인합니다.
- 날짜, 금액, 타입, 카테고리를 검증합니다.
- 잘못된 행을 어떻게 처리할지 정합니다.

export에서 조심할 점:

- `--month` 또는 `--from`/`--to` 조건을 받습니다.
- UTF-8로 저장합니다.
- 헤더를 포함합니다.
- 처리한 건수를 출력합니다.

## 17. 정렬과 최신순 출력

`list`와 `search` 결과는 최신순으로 출력해야 합니다.

최신순 정렬은 보통 날짜 기준 내림차순입니다.

```python
sorted_transactions = sorted(
    transactions,
    key=lambda transaction: transaction.date,
    reverse=True,
)
```

단, 스트리밍 처리 요구사항이 있으므로 구현 방식에 주의해야 합니다. 파일 전체를 무조건 리스트로 바꾸는 방식은 대용량 처리 관점에서 약점이 있습니다.

과제 규모에서는 다음 중 하나를 선택할 수 있습니다.

- 저장할 때 최신 거래가 위로 오도록 관리합니다.
- 출력 직전에 필요한 범위만 모읍니다.
- 검색 결과만 제한적으로 모아서 정렬합니다.

요구사항의 의도는 “처음부터 모든 데이터를 무조건 메모리에 올리는 습관을 피하라”는 것입니다.

## 18. 테스트 관점

과제에 테스트 파일이 필수라고 명시되어 있지는 않지만, 직접 확인할 시나리오는 준비하는 것이 좋습니다.

확인할 주요 시나리오:

- 카테고리 추가 후 목록 조회
- 등록되지 않은 카테고리로 거래 추가 시 실패
- 거래 추가 후 id 출력
- list 최신순 출력
- search 조건별 필터링
- summary 총수입, 총지출, 잔액 계산
- budget 설정 후 summary에서 사용률 출력
- 없는 id update/delete 처리
- import/export CSV 처리
- 잘못된 날짜, 금액, 타입 입력 처리

테스트는 기능이 많아질수록 실수를 줄여주는 안전장치입니다.

## 19. 구현 우선순위

처음부터 모든 기능을 한 번에 만들기보다 아래 순서로 진행하면 좋습니다.

1. 프로젝트 구조 만들기
2. 데이터 모델 정의
3. 카테고리 저장/조회 구현
4. 거래 추가 구현
5. 거래 목록 조회 구현
6. 검색 구현
7. 월별 요약 구현
8. 예산 설정과 summary 연동
9. update/delete 구현
10. import/export 구현
11. 데코레이터 적용
12. README 작성

## 20. 핵심 요약

이 과제에서 가장 중요한 CS 개념은 다음과 같습니다.

- 파일 입출력과 영구 저장
- CSV/JSONL 데이터 형식
- CRUD
- 데이터 모델링
- 타입 힌트
- 모듈화와 책임 분리
- 제너레이터와 스트리밍 처리
- 검색, 필터링, 집계
- CLI 설계
- 입력 검증
- 예외 처리와 종료 코드
- 데코레이터
- 데이터 무결성
- 파일 안전성

큰 그림은 아래 구조로 기억하면 됩니다.

```text
사용자 명령
  -> CLI
  -> Service
  -> Repository
  -> File
```

이 구조를 지키면 기능이 많아져도 코드가 덜 복잡해지고, 과제에서 요구하는 유지보수 가능한 설계에 가까워집니다.
