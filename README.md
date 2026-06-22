# File-based Household Ledger Console

Python 표준 라이브러리만 사용한 파일 기반 가계부 콘솔 프로그램입니다.

## 실행 방법

Python 3.10 이상에서 실행합니다.

```bash
python3 -m budget_app --help
python3 -m budget_app add
python3 -m budget_app list --limit 5
```

저장 디렉토리를 바꾸고 싶으면 전역 옵션 `--data-dir`를 사용합니다.

```bash
python3 -m budget_app --data-dir ./my_data list
```

## 저장 파일

기본 저장 위치는 `./data`입니다. 프로그램 실행 시 파일이 없으면 자동 생성됩니다.

```text
data/
  transactions.jsonl
  categories.jsonl
  budgets.jsonl
```

내부 저장 형식은 JSONL입니다. 한 줄에 JSON 객체 하나를 저장합니다.

거래 데이터 예:

```json
{"id":"TX-000001","date":"2024-01-15","type":"expense","category":"food","amount":15000,"memo":"점심","tags":["meal"]}
```

카테고리 파일이 비어 있으면 기본 카테고리를 자동 생성합니다.

```text
food, transport, rent, salary, etc
```

## 주요 명령 예시

거래 추가는 대화형 입력으로 진행합니다.

```bash
python3 -m budget_app add
```

거래 목록:

```bash
python3 -m budget_app list --limit 3
```

거래 검색:

```bash
python3 -m budget_app search --from 2024-01-01 --to 2024-01-31 --category food
python3 -m budget_app search --type expense --tag meal
```

월별 요약:

```bash
python3 -m budget_app summary --month 2024-01 --top 3
```

예산 설정:

```bash
python3 -m budget_app budget set --month 2024-01 --amount 500000
python3 -m budget_app budget list
python3 -m budget_app budget show --month 2024-01
```

`summary --month YYYY-MM` 실행 시 해당 월 예산이 설정되어 있으면 예산 금액, 지출 대비 사용률, 초과 여부를 함께 출력합니다. 예산을 초과한 경우 `[경고] 예산을 초과했습니다.` 문구가 표시됩니다.

카테고리 관리:

```bash
python3 -m budget_app category list
python3 -m budget_app category add
python3 -m budget_app category remove --name food
```

카테고리 삭제 정책은 "사용 중이면 삭제 차단"입니다. `category remove --name <카테고리>` 실행 시 기존 거래에서 해당 카테고리를 사용 중이면 삭제하지 않고 오류 메시지와 해결 힌트를 출력합니다. 이 방식은 거래 데이터가 삭제된 카테고리를 참조하는 불일치를 막기 위한 정책입니다.

거래 수정은 옵션 방식으로 고정했습니다.

```bash
python3 -m budget_app update --id TX-000001 --amount 18000 --memo "저녁"
```

거래 삭제:

```bash
python3 -m budget_app delete --id TX-000001
```

CSV 가져오기/내보내기:

```bash
python3 -m budget_app import --from import.csv
python3 -m budget_app export --out export.csv --month 2024-01
python3 -m budget_app export --out export.csv --from 2024-01-01 --to 2024-01-31
```

## Import/Export CSV 스키마

CSV는 UTF-8, 헤더 포함 형식입니다.

| column | required | 설명 |
| --- | --- | --- |
| `date` | Y | `YYYY-MM-DD` |
| `type` | Y | `income` 또는 `expense` |
| `category` | Y | 등록된 카테고리 |
| `amount` | Y | 양수 정수 |
| `memo` | N | 문자열 |
| `tags` | N | 쉼표로 구분한 문자열 |

Import 동작은 부분 성공 방식입니다. CSV 전체 헤더에 필수 컬럼이 없으면 import를 시작하지 않고 오류로 종료합니다. 헤더는 맞지만 중간에 날짜, 타입, 카테고리, 금액 등이 잘못된 행이 섞여 있으면 해당 행만 건너뛰고 나머지 정상 행은 JSONL 저장소에 추가합니다. 실행 결과는 `imported=<성공 건수>, skipped=<건너뛴 건수>`로 출력합니다. 현재 구현은 이미 추가된 정상 행을 롤백하지 않습니다.

## 저장 형식 선택 근거

내부 저장 형식은 JSONL을 선택했습니다.

| 형식 | 장점 | 단점 | 이 프로젝트에서의 판단 |
| --- | --- | --- | --- |
| JSONL | 한 줄에 거래 1건을 저장하므로 `yield`로 스트리밍하기 쉽습니다. `tags` 같은 리스트 데이터를 자연스럽게 표현할 수 있습니다. | 일반 사용자가 스프레드시트에서 직접 열어보기에는 CSV보다 덜 익숙합니다. | 내부 저장소에 적합합니다. `Transaction.to_dict()` / `from_dict()`와 잘 맞고, 리스트 필드를 그대로 보존할 수 있습니다. |
| CSV | 스프레드시트와 호환성이 좋고 사람이 표 형태로 확인하기 쉽습니다. | 리스트/중첩 구조 표현이 불편하고 쉼표, 줄바꿈, 따옴표 처리를 조심해야 합니다. | 외부 교환 형식에 적합합니다. 그래서 import/export 전용 포맷으로 사용합니다. |

정리하면, 앱 내부 데이터는 JSONL로 안전하게 유지하고 외부 파일 교환은 CSV로 처리합니다.

## 오류 처리와 종료 코드

오류는 스택트레이스를 그대로 노출하지 않고 사용자에게 원인과 해결 힌트를 출력합니다. 이 공통 처리는 `decorators.py`의 `handle_errors` 데코레이터가 담당합니다.

예시:

```text
[오류] 날짜 형식이 올바르지 않습니다.
[힌트] 예: 2024-01-15
```

처리하는 대표 오류:

| 오류 상황 | 처리 방식 |
| --- | --- |
| 잘못된 날짜, 월, 금액, 타입 | `[오류]`와 `[힌트]` 출력 후 종료 |
| 없는 거래 id 수정/삭제 | 없는 데이터임을 출력 후 종료 |
| 없는 파일 | 파일 경로 확인 힌트 출력 |
| 권한 오류 | 권한 또는 경로 확인 힌트 출력 |
| 깨진 JSONL | 저장 파일 형식 확인 힌트 출력 |
| 깨진 CSV | UTF-8, 헤더 포함, 쉼표 구분 형식 확인 힌트 출력 |
| 입력 중단 | 필요한 값을 끝까지 입력하라는 힌트 출력 |

종료 코드는 `__main__.py`의 `raise SystemExit(main())`로 운영체제에 전달됩니다. 정상 처리 시 각 명령은 `0`을 반환하고, `handle_errors`가 잡은 오류 상황은 `1`을 반환합니다. 따라서 오류 종료 시 exit code는 0이 아닙니다.

```text
0 = 정상 종료
1 = 오류 종료
```

## 타입 힌트

프로젝트 전반에 타입 힌트를 적용해 함수의 입력과 출력 계약을 명확히 했습니다. 예를 들어 `services.py`의 거래 추가 함수는 입력값과 반환 모델을 다음처럼 드러냅니다.

```python
def add_transaction(
    self,
    date: str,
    type_: str,
    category: str,
    amount: str | int,
    memo: str = "",
    tags: str | None = None,
) -> Transaction:
    ...
```

타입 힌트를 통해 얻는 이점:

- CLI 입력은 문자열이지만 서비스 내부에서 어떤 타입으로 변환되는지 추적하기 쉽습니다.
- `Transaction`, `Budget`, `SearchCriteria` 같은 데이터 모델의 사용 위치가 명확해집니다.
- `Transaction | None`, `Iterator[Transaction]`, `Iterable[Transaction]`처럼 데이터가 없을 수 있는 경우와 스트리밍 반환을 코드에서 표현할 수 있습니다.
- IDE 자동완성, 정적 분석, 리팩터링 시 실수 방지에 도움이 됩니다.

## 구조

```text
budget_app/
  __main__.py
  cli.py
  decorators.py
  errors.py
  models.py
  repositories.py
  services.py
  sorting.py
  validators.py
```

큰 흐름은 다음과 같습니다.

```text
CLI -> Service -> Repository -> JSONL File
```

## Python 파일별 역할

| 파일 | 역할 |
| --- | --- |
| `budget_app/__init__.py` | `budget_app` 디렉토리를 Python 패키지로 인식하게 하는 파일입니다. |
| `budget_app/__main__.py` | `python3 -m budget_app` 실행 시 호출되는 진입점입니다. 내부에서 `cli.main()`을 실행합니다. |
| `budget_app/cli.py` | 터미널 명령어와 옵션을 정의합니다. `ParserBuilder`, `ServiceFactory`, `CommandRunner`, `ConsolePrinter`로 CLI 구성, 서비스 조립, 실행, 출력을 나눕니다. |
| `budget_app/models.py` | `Transaction`, `Budget`, `SearchCriteria` 같은 데이터 구조를 `dataclass`로 정의합니다. |
| `budget_app/repositories.py` | JSONL 저장 파일을 생성, 읽기, 추가, 재작성합니다. 거래 데이터는 `yield`로 한 줄씩 스트리밍합니다. |
| `budget_app/services.py` | 거래 추가, 목록, 검색, 요약, 예산, 카테고리, import/export 같은 핵심 기능 로직을 담당합니다. |
| `budget_app/validators.py` | 날짜, 월, 금액, 거래 타입, 태그 같은 사용자 입력값을 검증하고 변환합니다. |
| `budget_app/decorators.py` | 예외 처리와 실행 시간 측정처럼 여러 명령어에 공통으로 적용되는 기능을 데코레이터로 분리합니다. |
| `budget_app/errors.py` | 사용자에게 보여줄 수 있는 애플리케이션 전용 예외 클래스를 정의합니다. |
| `budget_app/sorting.py` | 최신순 출력을 위한 정렬 유틸리티입니다. `list --limit`는 heap으로 최신 N개만 유지하고, `search`/`export`는 chunk 단위 임시 파일 정렬을 사용합니다. |

`repositories.py`는 JSONL 파일을 제너레이터로 한 줄씩 읽습니다. `list --limit`는 필요한 개수만 메모리에 유지하고, `search`와 `export`는 chunk 단위 임시 파일 정렬로 최신순을 유지합니다. 파일 전체를 하나의 리스트로 한 번에 로드하지 않습니다.

`update`는 옵션 기반으로 고정했습니다. 수정할 필드를 하나 이상 입력해야 합니다.

`update`와 `delete`는 임시 파일에 새 내용을 쓴 뒤 `os.replace()`로 교체합니다.

## 대용량 데이터 고려

거래가 10만 건 이상으로 늘어났을 때 예상되는 병목과 현재 대응 방식은 다음과 같습니다.

| 병목 지점 | 현재 대응 | 추가 개선 방안 |
| --- | --- | --- |
| 파일 전체를 한 번에 읽는 문제 | `TransactionRepository.iter_all()`이 `yield`로 JSONL을 한 줄씩 스트리밍합니다. | 월별 파일 분할 또는 인덱스 파일을 둘 수 있습니다. |
| `list --limit` 최신 N개 조회 | `heapq.nlargest()`로 전체 정렬 대신 최신 N개만 유지합니다. | 거래 저장 시 최신순 append 정책을 별도로 설계하면 더 빠르게 만들 수 있습니다. |
| `search` / `export` 최신순 정렬 | `sorting.py`에서 chunk 단위 임시 파일 정렬 후 병합합니다. | 검색 조건별 인덱스 또는 SQLite 같은 DB 도입을 고려할 수 있습니다. |
| `next_id()`가 매번 전체 거래를 순회 | 현재는 기존 id 중 최댓값을 찾기 위해 전체 거래를 읽습니다. | 별도 metadata 파일에 마지막 id를 저장하면 O(1)에 가까워집니다. |
| `update/delete` 전체 재작성 | 임시 파일 + `os.replace()`로 안전성을 우선합니다. | 데이터가 매우 커지면 DB 또는 append-only 로그 + compaction 구조가 적합합니다. |

현재 과제는 파일 기반 저장과 표준 라이브러리만 사용하는 조건이 있으므로, 안전성과 요구사항 충족을 우선해 JSONL 스트리밍, heap, chunk 정렬, 원자적 교체를 사용했습니다.
