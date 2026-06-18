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

카테고리 관리:

```bash
python3 -m budget_app category list
python3 -m budget_app category add
python3 -m budget_app category remove --name food
```

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
