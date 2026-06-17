# `yield` in Python

## What is `yield`?
`yield`는 **제너레이터**를 만들 때 사용하는 키워드로, 함수를 바로 종료하지 않고 현재 값을 호출자에게 반환하고 함수의 상태를 그대로 보존합니다. `yield`가 하나라도 있으면 그 함수는 제너레이터 객체를 반환합니다.

## Key Characteristics
| Feature | Description |
|---------|-------------|
| **Value Return** | `return`과 달리 함수를 종료하지 않고, 현재 값을 반환하고 일시 중단합니다. |
| **Generator Function** | `yield`가 포함된 함수는 호출 시 바로 실행되지 않고 **제너레이터 객체**를 반환합니다. |
| **Lazy Evaluation** | 값이 필요할 때마다 하나씩 생성하므로 메모리를 절약하고 무한 시퀀스를 구현할 수 있습니다. |

## Simple Example
```python
def count_up_to(n):
    i = 1
    while i <= n:
        yield i  # 현재 i를 반환하고 일시 중단
        i += 1

# 사용 예시
for num in count_up_to(5):
    print(num)
```
**Output:**
```
1
2
3
4
5
```
- `count_up_to`는 호출 시 제너레이터 객체를 반환합니다.
- `for` 루프가 `next()`를 호출할 때마다 `yield`가 실행돼 다음 값을 얻고, 함수는 그 지점에서 멈춥니다.
- `yield`가 끝에 도달하면 `StopIteration` 예외가 자동으로 발생해 반복이 종료됩니다.

## When to Use `yield`
- **Large Data**: 한 번에 메모리로 로드하고 싶지 않을 때.
- **Infinite Sequences**: 실시간 센서 데이터, 스트리밍 등 무한히 생성되는 시퀀스를 만들 때.
- **Complex Flow Control**: `return`만으로는 표현하기 어려운 흐름 제어가 필요할 때.

## Summary
`yield`는 함수 실행을 일시 중단하고 현재 값을 반환하면서, 이후 재개 가능한 **제너레이터**를 만들기 위한 키워드입니다. 이를 통해 메모리 효율적인 순차 연산과 무한 시퀀스 구현이 가능합니다.
