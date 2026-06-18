# File-based Household Ledger Console

Python 표준 라이브러리만 사용한 파일 기반 가계부 콘솔 프로그램입니다.

## 실행 방법

Python 3.10 이상에서 실행합니다.

```bash
python -m budget_app --help
python -m budget_app add
python -m budget_app list --limit 5
```

저장 디렉토리를 바꾸고 싶으면 전역 옵션 `--data-dir`를 사용합니다.

```bash
python -m budget_app --data-dir ./my_data list
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
python -m budget_app add
```

거래 목록:

```bash
python -m budget_app list --limit 3
```

거래 검색:

```bash
python -m budget_app search --from 2024-01-01 --to 2024-01-31 --category food
python -m budget_app search --type expense --tag meal
```

월별 요약:

```bash
python -m budget_app summary --month 2024-01 --top 3
```

예산 설정:

```bash
python -m budget_app budget set --month 2024-01 --amount 500000
```

카테고리 관리:

```bash
python -m budget_app category list
python -m budget_app category add
python -m budget_app category remove --name food
```

거래 수정은 옵션 방식으로 고정했습니다.

```bash
python -m budget_app update --id TX-000001 --amount 18000 --memo "저녁"
```

거래 삭제:

```bash
python -m budget_app delete --id TX-000001
```

CSV 가져오기/내보내기:

```bash
python -m budget_app import --from import.csv
python -m budget_app export --out export.csv --month 2024-01
python -m budget_app export --out export.csv --from 2024-01-01 --to 2024-01-31
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
  validators.py
```

큰 흐름은 다음과 같습니다.

```text
CLI -> Service -> Repository -> JSONL File
```

`repositories.py`는 JSONL 파일을 제너레이터로 한 줄씩 읽습니다. `update`와 `delete`는 임시 파일에 새 내용을 쓴 뒤 `os.replace()`로 교체합니다.
