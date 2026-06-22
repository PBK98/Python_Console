# 2-1 평가 문항 답변

이 문서는 파일 기반 가계부 콘솔 프로그램의 평가 문항에 대한 답변입니다. 현재 프로젝트 구현 기준으로 작성했습니다.

## 항목 1. 필수 기능 동작과 저장 유지

### add/list/search/summary/export/import/update/delete가 요구사항대로 동작하는가?

구현되어 있습니다.

주요 실행 예시는 다음과 같습니다.

```bash
python3 -m budget_app add
python3 -m budget_app list --limit 3
python3 -m budget_app search --from 2024-01-01 --to 2024-01-31 --category food
python3 -m budget_app summary --month 2024-01 --top 3
python3 -m budget_app export --out export.csv --month 2024-01
python3 -m budget_app import --from import.csv
python3 -m budget_app update --id TX-000001 --amount 18000 --memo "저녁"
python3 -m budget_app delete --id TX-000001
```

명령어 처리는 `budget_app/cli.py`의 `ParserBuilder`와 `CommandRunner`가 담당합니다. 실제 기능 로직은 `budget_app/services.py`의 `TransactionService`, `CategoryService`, `BudgetService`에 분리되어 있습니다.

### 프로그램 재실행 후에도 데이터가 유지되는가?

유지됩니다. 데이터는 기본적으로 `./data` 디렉토리에 JSONL 파일로 저장됩니다.

```text
data/
  transactions.jsonl
  categories.jsonl
  budgets.jsonl
```

거래, 카테고리, 예산을 각각 별도 파일로 저장하므로 프로그램을 종료했다가 다시 실행해도 데이터가 유지됩니다.

### category add/list/remove가 정상 동작하는가?

구현되어 있습니다.

```bash
python3 -m budget_app category add
python3 -m budget_app category list
python3 -m budget_app category remove --name food
```

카테고리 삭제 정책은 **사용 중이면 삭제 차단**입니다. `CategoryService.remove_category()`는 기존 거래를 순회하면서 해당 카테고리를 사용하는 거래가 있는지 확인합니다. 사용 중이면 삭제하지 않고 다음과 같은 오류를 출력합니다.

```text
[오류] 사용 중인 카테고리는 삭제할 수 없습니다.
[힌트] 먼저 해당 거래를 수정하거나 삭제하세요.
```

이 방식은 거래 데이터가 존재하지 않는 카테고리를 참조하는 불일치를 막기 위한 처리입니다.

### budget set이 저장되며 summary에서 예산 사용률/초과 여부가 출력되는가?

구현되어 있습니다.

```bash
python3 -m budget_app budget set --month 2024-01 --amount 500000
python3 -m budget_app summary --month 2024-01 --top 3
```

`BudgetService.set_budget()`은 월별 예산을 `budgets.jsonl`에 저장합니다. 이후 `TransactionService.summarize()`는 해당 월의 예산을 조회해 총지출 대비 사용률을 계산합니다.

예상 출력 예:

```text
총 수입: 3000000원
총 지출: 215000원
잔액: 2785000원
예산: 500000원 (사용률 43.0%)
```

예산을 초과하면 다음 경고도 함께 출력됩니다.

```text
[경고] 예산을 초과했습니다.
```

### import/export가 명시된 CSV 스키마로 동작하는가?

동작합니다. CSV는 UTF-8, 헤더 포함 형식입니다.

| column | required | 설명 |
| --- | --- | --- |
| `date` | Y | `YYYY-MM-DD` |
| `type` | Y | `income` 또는 `expense` |
| `category` | Y | 등록된 카테고리 |
| `amount` | Y | 양수 정수 |
| `memo` | N | 문자열 |
| `tags` | N | 쉼표로 구분한 문자열 |

내부 저장은 JSONL이지만, 외부 입출력은 CSV로 처리합니다.

```text
import: CSV -> 검증 -> Transaction -> transactions.jsonl
export: transactions.jsonl -> 조건 필터링 -> CSV
```

### 잘못된 입력/파일 오류에서 스택트레이스 없이 오류 메시지와 힌트를 출력하는가?

구현되어 있습니다. `budget_app/decorators.py`의 `handle_errors` 데코레이터가 공통 오류 처리를 담당합니다.

예:

```text
[오류] 날짜 형식이 올바르지 않습니다.
[힌트] 예: 2024-01-15
```

처리하는 대표 오류는 다음과 같습니다.

| 오류 상황 | 처리 |
| --- | --- |
| 잘못된 날짜, 월, 금액, 타입 | 오류 메시지와 입력 예시 출력 |
| 없는 id 수정/삭제 | 없는 데이터임을 출력 |
| 파일 없음 | 경로 확인 힌트 출력 |
| 권한 오류 | 권한 또는 경로 확인 힌트 출력 |
| 깨진 JSONL | 저장 파일 형식 확인 힌트 출력 |
| 깨진 CSV | CSV 형식 확인 힌트 출력 |
| 입력 중단 | 필요한 값을 끝까지 입력하라는 힌트 출력 |

### 오류 상황에서 종료 코드가 0이 아님을 확인할 수 있는가?

확인할 수 있습니다.

`budget_app/__main__.py`는 다음처럼 `main()`의 반환값을 운영체제 종료 코드로 전달합니다.

```python
raise SystemExit(main())
```

정상 처리 시에는 `0`을 반환하고, `handle_errors`가 잡은 오류 상황에서는 `1`을 반환합니다.

```text
0 = 정상 종료
1 = 오류 종료
```

따라서 잘못된 입력이나 파일 오류가 발생하면 종료 코드는 0이 아닙니다.

## 항목 2. 모듈 분리, 클래스 책임, 파일 기반 update/delete 안전성

### 코드가 3개 이상 모듈로 분리되어 있고 각 모듈 책임을 설명할 수 있는가?

분리되어 있습니다.

| 파일 | 책임 |
| --- | --- |
| `__main__.py` | `python3 -m budget_app` 실행 진입점 |
| `cli.py` | 명령어 정의, 인자 파싱, service 호출 |
| `models.py` | `Transaction`, `Budget`, `SearchCriteria` 데이터 모델 |
| `repositories.py` | JSONL 파일 읽기/쓰기 |
| `services.py` | 거래/카테고리/예산 비즈니스 로직 |
| `validators.py` | 날짜, 금액, 타입 등 입력 검증 |
| `sorting.py` | 최신순 정렬, heap, chunk 정렬 |
| `decorators.py` | 예외 처리, 실행 시간 측정 |
| `errors.py` | 앱 전용 예외 클래스 |

큰 흐름은 다음과 같습니다.

```text
CLI -> Service -> Repository -> JSONL File
```

### 최소 2개 이상의 클래스에 부여한 책임 경계를 설명할 수 있는가?

설명할 수 있습니다.

| 클래스 | 책임 |
| --- | --- |
| `ParserBuilder` | CLI 명령어와 옵션 구성 |
| `ServiceFactory` | 저장소와 서비스 객체 조립 |
| `CommandRunner` | 파싱된 명령어를 실제 service 호출로 연결 |
| `ConsolePrinter` | 거래/예산 출력 형식 관리 |
| `TransactionService` | 거래 추가, 목록, 검색, 요약, 수정, 삭제, import/export |
| `CategoryService` | 카테고리 추가, 목록, 삭제 규칙 |
| `BudgetService` | 월별 예산 저장/조회 |
| `TransactionRepository` | 거래 JSONL 파일 읽기/추가/재작성 |
| `CategoryRepository` | 카테고리 JSONL 파일 읽기/쓰기 |
| `BudgetRepository` | 예산 JSONL 파일 읽기/쓰기 |

CLI, 비즈니스 로직, 파일 입출력을 분리해 각 계층이 한 가지 책임에 집중하도록 구성했습니다.

### 파일 기반 update/delete를 어떻게 안전하게 처리했는가?

`TransactionRepository.rewrite()`에서 임시 파일을 사용합니다.

처리 흐름:

```text
1. 기존 transactions.jsonl을 한 줄씩 읽는다.
2. 수정/삭제 결과를 임시 파일에 쓴다.
3. 쓰기가 모두 성공하면 os.replace()로 원본 파일을 교체한다.
4. 중간에 오류가 나면 임시 파일을 삭제하고 원본은 유지한다.
```

이 방식은 파일이 반쯤만 저장되는 상황을 줄이고, update/delete 중 오류가 발생했을 때 원본 파일을 보호합니다.

## 항목 3. 제너레이터, 데코레이터, 타입 힌트

### list/search를 제너레이터로 스트리밍 처리한 방식과 이유는?

`TransactionRepository.iter_all()`은 `yield`를 사용해 거래 파일을 한 줄씩 읽습니다.

```python
def iter_all(self) -> Iterator[Transaction]:
    with self.store.transactions_path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                yield Transaction.from_dict(json.loads(line))
```

이 방식은 파일 전체를 한 번에 리스트로 올리지 않고, 필요한 거래를 하나씩 처리합니다. 거래 수가 많아져도 메모리 사용량을 줄일 수 있습니다.

`list --limit`는 `heapq.nlargest()`로 최신 N개만 메모리에 유지합니다. `search`와 `export`는 `sorting.py`의 chunk 단위 임시 파일 정렬을 사용해 최신순 결과를 만듭니다.

### 데코레이터로 분리한 공통 기능과 분리 이유는?

`decorators.py`에서 두 가지 공통 기능을 분리했습니다.

| 데코레이터 | 역할 |
| --- | --- |
| `handle_errors` | 예외를 잡아 스택트레이스 대신 오류 메시지와 힌트 출력 |
| `measure_time` | 명령 실행 시간 출력 |

`cli.py`의 `run()`에 적용되어 모든 CLI 명령에 공통으로 적용됩니다.

```python
@handle_errors
@measure_time
def run(args: argparse.Namespace) -> int:
    return CommandRunner().run(args)
```

이렇게 분리하면 add/list/search 등 각 명령에 반복적으로 `try/except`와 시간 측정 코드를 작성하지 않아도 됩니다. 핵심 기능 로직과 공통 관심사를 분리할 수 있습니다.

### 타입 힌트를 적용해 얻는 이점과 코드 예시는?

타입 힌트는 함수의 입력과 출력 계약을 명확히 합니다.

예:

```python
def search(self, criteria: SearchCriteria) -> Iterator[Transaction]:
    ...
```

이 함수는 `SearchCriteria`를 받아 `Transaction`을 하나씩 반환하는 제너레이터라는 뜻입니다.

또 다른 예:

```python
def show_budget(self, month: str) -> Budget | None:
    ...
```

예산이 있으면 `Budget`, 없으면 `None`을 반환할 수 있음을 드러냅니다.

이점:

- 함수가 어떤 값을 받고 반환하는지 빠르게 이해할 수 있습니다.
- IDE 자동완성과 정적 분석에 도움이 됩니다.
- `None` 가능성, 제너레이터 반환, 모델 사용 위치를 명확히 표현할 수 있습니다.
- 리팩터링 시 잘못된 타입 사용을 빨리 발견할 수 있습니다.

## 항목 4. 저장 포맷 선택, 대용량 병목, import 깨진 행 처리

### JSONL과 CSV의 장단점 비교 및 선택 근거는?

| 형식 | 장점 | 단점 | 선택 판단 |
| --- | --- | --- | --- |
| JSONL | 한 줄에 객체 1개를 저장하므로 스트리밍 처리에 유리합니다. `tags` 같은 리스트 데이터를 자연스럽게 저장할 수 있습니다. | 스프레드시트에서 바로 보기에는 CSV보다 덜 익숙합니다. | 내부 저장소로 선택했습니다. |
| CSV | 사람이 표 형태로 보기 쉽고 스프레드시트와 호환됩니다. | 리스트/중첩 구조 표현이 불편하고 쉼표, 따옴표, 줄바꿈 처리를 조심해야 합니다. | import/export용 외부 교환 형식으로 사용했습니다. |

따라서 내부 저장은 JSONL, 외부 입출력은 CSV로 역할을 나누었습니다.

```text
내부 저장: transactions.jsonl, categories.jsonl, budgets.jsonl
외부 교환: import.csv, export.csv
```

### 거래가 10만 건으로 늘어나면 병목은 어디이고 어떻게 개선할 수 있는가?

예상 병목과 대응 방안은 다음과 같습니다.

| 병목 | 현재 대응 | 개선 방안 |
| --- | --- | --- |
| 전체 파일 읽기 | `yield`로 한 줄씩 스트리밍 | 월별 파일 분할, 인덱스 파일 |
| 최신순 list | `heapq.nlargest()`로 최신 N개만 유지 | 저장 시 최신순 유지, metadata 활용 |
| search/export 정렬 | chunk 임시 파일 정렬 후 병합 | 검색 인덱스, SQLite 도입 |
| id 생성 | 기존 id 최댓값을 찾기 위해 전체 순회 | metadata 파일에 마지막 id 저장 |
| update/delete | 파일 전체 재작성 | append-only 로그 + compaction, DB 도입 |

현재 과제는 표준 라이브러리와 파일 기반 저장 조건이 있으므로, JSONL 스트리밍, heap, chunk 정렬, 임시 파일 교체로 대응했습니다.

### import CSV에 일부 깨진 행이 섞이면 어떻게 처리하는가?

현재 구현은 **부분 성공 방식**입니다.

처리 방식:

```text
1. CSV 헤더에 필수 컬럼(date, type, category, amount)이 없으면 전체 import를 시작하지 않고 오류 종료한다.
2. 헤더는 정상인데 일부 행의 날짜, 타입, 카테고리, 금액이 잘못되면 해당 행만 건너뛴다.
3. 정상 행은 transactions.jsonl에 추가한다.
4. 결과로 imported, skipped 건수를 출력한다.
```

예:

```text
[완료] imported=5, skipped=2
```

현재 구현은 이미 import된 정상 행을 롤백하지 않습니다. 대신 잘못된 행을 건너뛰고 성공/실패 건수를 명확히 알려 사용자 신뢰를 유지합니다.

## 항목 5. 보너스 문제 해결 크레딧

보너스에 해당할 수 있는 구현 요소는 다음과 같습니다.

- `update/delete`에서 임시 파일과 `os.replace()`를 사용해 원자적 교체 방식 적용

