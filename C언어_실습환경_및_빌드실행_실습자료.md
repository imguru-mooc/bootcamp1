# C 언어 실습 환경 구축 및 빌드 · 실행

**로봇 플랫폼 (Robot Platform) · 임베디드 리눅스 실습 자료**
운영체제: **Ubuntu 22.04 LTS** (데스크톱 PC · 라즈베리파이 4 · Jetson Orin Nano 공통)

> 본 자료는 *개발 환경 설정 및 테스트* 실습에 이어, **C 언어 컴파일/실행에 집중**한 실습 자료입니다.
> 임베디드 리눅스에서 C는 GPIO 제어, 디바이스 드라이버, 시스템 프로그래밍의 기반이 됩니다.
> 명령을 한 줄씩 직접 입력하며 따라 하고, 각 단계 끝의 **체크포인트**에서 정상 동작을 확인하세요.

---

## 학습 목표

이 실습을 마치면 다음을 할 수 있습니다.

- C 컴파일 환경(gcc)을 점검하고, 없으면 설치한다.
- 첫 C 프로그램을 **작성 → 컴파일 → 실행** 하는 전체 흐름을 익힌다.
- `gcc`의 자주 쓰는 옵션(`-o`, `-Wall`, `-g`, `-O2`)을 이해하고 사용한다.
- 컴파일의 4단계(전처리·컴파일·어셈블·링크)를 직접 눈으로 확인한다.
- 여러 소스 파일을 나눠 컴파일하고 하나의 실행 파일로 링크한다.
- `Makefile`로 빌드를 자동화한다.
- 컴파일 에러 메시지를 읽고 스스로 해결한다.

---

## 표기 약속

```bash
$           # 일반 사용자 프롬프트 (직접 입력하는 명령)
#           # 주석 — 입력하지 않습니다 (설명용)
출력 ▶      # 명령 실행 후 화면에 나타나는 예시 결과
```

---

## 실습 1 · C 컴파일 환경 점검 & 설치

C 컴파일러 **gcc**가 설치되어 있는지 먼저 확인합니다.

```bash
# gcc 버전 확인
$ gcc --version
출력 ▶ gcc (Ubuntu 11.4.0-...) 11.4.0
```

만약 `command not found` 가 나오면 설치합니다.

```bash
# 빌드 도구 묶음 설치 (gcc, make 등 포함)
$ sudo apt update
$ sudo apt install -y build-essential

# 다시 확인
$ gcc --version
```

> 💡 `build-essential` 에는 `gcc`(C 컴파일러), `g++`(C++ 컴파일러), `make`(빌드 자동화), 표준 라이브러리 헤더가 포함됩니다.

작업 폴더를 만들어 둡니다.

```bash
$ mkdir -p ~/c_practice && cd ~/c_practice
```

> ✅ **체크포인트 1**
> `gcc --version` 이 버전 번호를 출력하고, `~/c_practice` 폴더로 이동했으면 통과입니다.

---

## 실습 2 · 첫 C 프로그램 — 작성 → 컴파일 → 실행

C 개발은 **세 단계**로 이뤄집니다. 이 흐름을 몸에 익히는 것이 이번 실습의 핵심입니다.

```text
[1] 소스 작성        [2] 컴파일             [3] 실행
hello.c    ──gcc──▶  hello(실행파일)  ──▶  화면 출력
(사람이 읽는 코드)   (기계가 읽는 코드)
```

### 2-1. 소스 코드 작성

```bash
$ nano hello.c
```

```c
#include <stdio.h>

int main(void) {
    printf("Hello, Robot!\n");
    return 0;
}
```

저장: `Ctrl+O` → `Enter`, 종료: `Ctrl+X`

### 2-2. 컴파일

```bash
# hello.c 를 컴파일해서 'hello' 라는 실행 파일 생성
$ gcc hello.c -o hello
```

- `-o hello` : 출력(output) 실행 파일 이름을 `hello`로 지정
- `-o` 를 생략하면 기본 이름 **`a.out`** 으로 만들어집니다.

### 2-3. 실행

```bash
# 현재 폴더(./)의 hello 실행
$ ./hello
출력 ▶ Hello, Robot!
```

> 💡 리눅스는 보안을 위해 현재 폴더를 자동으로 실행 경로에 넣지 않습니다.
> 그래서 실행 파일 앞에 **`./`** (현재 디렉터리)를 반드시 붙입니다.

### 코드 한 줄씩 이해하기

| 코드 | 의미 |
|---|---|
| `#include <stdio.h>` | 표준 입출력 함수(`printf` 등)를 사용하기 위한 헤더 포함 |
| `int main(void)` | 프로그램이 시작되는 진입점 함수 |
| `printf("...\n")` | 화면에 문자열 출력 (`\n` = 줄바꿈) |
| `return 0;` | 정상 종료를 의미하는 반환값(0) |

> ✅ **체크포인트 2**
> `./hello` 실행 시 `Hello, Robot!` 이 출력되면 통과입니다.
> `Permission denied` 가 나오면 → `chmod +x hello` 후 다시 실행하세요.

---

## 실습 3 · gcc 자주 쓰는 옵션

실무에서 거의 항상 쓰는 옵션들입니다. 특히 **`-Wall`** 은 습관화하세요.

| 옵션 | 의미 | 권장 |
|---|---|---|
| `-o 이름` | 실행 파일 이름 지정 | 항상 |
| `-Wall` | 모든 경고(warning) 표시 | **항상** |
| `-Wextra` | 추가 경고까지 표시 | 권장 |
| `-g` | 디버깅 정보 포함 (gdb용) | 디버깅 시 |
| `-O2` | 최적화(속도 향상) | 배포 시 |
| `-std=c11` | C 표준 버전 지정 | 권장 |

### 경고(-Wall) 체험하기

일부러 문제가 있는 코드를 작성해 봅니다.

```bash
$ nano warn.c
```

```c
#include <stdio.h>

int main(void) {
    int x;                      // 값을 넣지 않음
    printf("x = %d\n", x);      // 초기화 안 된 변수 사용
    return 0;
}
```

```bash
# 경고 없이 컴파일 — 문제를 그냥 지나침
$ gcc warn.c -o warn

# -Wall 로 컴파일 — 경고가 나타남
$ gcc -Wall warn.c -o warn
출력 ▶ warning: 'x' is used uninitialized in this function
```

> 💡 권장 컴파일 형식:
> ```bash
> $ gcc -Wall -Wextra -std=c11 warn.c -o warn
> ```

> ✅ **체크포인트 3**
> `-Wall` 을 붙였을 때 경고 메시지가 나타나는 것을 확인하면 통과입니다.
> **경고는 버그의 신호입니다. 무시하지 말고 고치는 습관**을 들이세요.

---

## 실습 4 · 컴파일의 4단계 (심화)

`gcc` 한 번의 명령은 사실 **4단계**를 거칩니다. 각 단계를 직접 확인해 봅니다.

```text
hello.c ─[1.전처리]→ hello.i ─[2.컴파일]→ hello.s ─[3.어셈블]→ hello.o ─[4.링크]→ hello
 소스           #include 처리      어셈블리 코드        기계어(목적파일)       실행파일
```

```bash
# 1) 전처리만 (#include, #define 처리) → .i
$ gcc -E hello.c -o hello.i

# 2) 컴파일까지 (어셈블리 생성) → .s
$ gcc -S hello.c -o hello.s

# 3) 어셈블까지 (목적 파일 생성) → .o
$ gcc -c hello.c -o hello.o

# 4) 링크 (목적 파일 → 실행 파일)
$ gcc hello.o -o hello

# 생성된 파일들 확인
$ ls
출력 ▶ hello  hello.c  hello.i  hello.o  hello.s
```

| 단계 | 옵션 | 결과 파일 | 하는 일 |
|---|---|---|---|
| 전처리 | `-E` | `.i` | `#include`, `#define` 펼치기 |
| 컴파일 | `-S` | `.s` | 어셈블리 코드로 변환 |
| 어셈블 | `-c` | `.o` | 기계어(목적 파일) 생성 |
| 링크 | (없음) | 실행파일 | 라이브러리와 결합해 실행 파일 완성 |

> ✅ **체크포인트 4**
> `hello.i`, `hello.s`, `hello.o` 파일이 각각 생성되는 것을 확인하면 통과입니다.
> (`hello.s` 를 `cat` 으로 열어 어셈블리 코드를 구경해 보세요.)

---

## 실습 5 · 여러 소스 파일 나눠 컴파일

규모가 커지면 코드를 **여러 파일로 분리**합니다. C는 `.c`(구현)와 `.h`(선언)로 나눕니다.

세 개의 파일을 만듭니다.

### math_util.h (함수 선언)

```bash
$ nano math_util.h
```

```c
#ifndef MATH_UTIL_H
#define MATH_UTIL_H

int add(int a, int b);

#endif
```

### math_util.c (함수 구현)

```bash
$ nano math_util.c
```

```c
#include "math_util.h"

int add(int a, int b) {
    return a + b;
}
```

### main.c (메인 프로그램)

```bash
$ nano main.c
```

```c
#include <stdio.h>
#include "math_util.h"

int main(void) {
    int result = add(3, 4);
    printf("3 + 4 = %d\n", result);
    return 0;
}
```

### 컴파일 (두 가지 방법)

```bash
# 방법 A) 한 번에 컴파일 + 링크
$ gcc main.c math_util.c -o calc
$ ./calc
출력 ▶ 3 + 4 = 7

# 방법 B) 각각 목적 파일로 만든 뒤 링크 (대규모 프로젝트 방식)
$ gcc -c main.c            # → main.o
$ gcc -c math_util.c       # → math_util.o
$ gcc main.o math_util.o -o calc
$ ./calc
출력 ▶ 3 + 4 = 7
```

> 💡 방법 B의 장점: 수정한 파일만 다시 컴파일하면 되므로 **빌드 시간을 절약**합니다.
> 이 원리를 자동화한 것이 바로 다음에 배울 **Make** 입니다.

> ✅ **체크포인트 5**
> `./calc` 가 `3 + 4 = 7` 을 출력하면 통과입니다.

---

## 실습 6 · Make로 빌드 자동화

파일이 많아지면 매번 긴 `gcc` 명령을 입력하기 번거롭습니다. `Makefile`에 규칙을 적어 두면 **`make` 한 단어**로 빌드됩니다.

```bash
$ nano Makefile
```

```makefile
# 변수 정의
CC = gcc
CFLAGS = -Wall -Wextra -std=c11

# 기본 목표: 'make' 입력 시 실행됨
calc: main.o math_util.o
	$(CC) main.o math_util.o -o calc

main.o: main.c math_util.h
	$(CC) $(CFLAGS) -c main.c

math_util.o: math_util.c math_util.h
	$(CC) $(CFLAGS) -c math_util.c

# 'make clean' 입력 시 생성물 삭제
clean:
	rm -f calc *.o
```

> ⚠️ **중요**: 명령 줄(들여쓴 부분)은 반드시 **스페이스가 아닌 Tab** 으로 들여써야 합니다.
> nano에서 Tab 키를 눌러 입력하세요. (스페이스면 `missing separator` 오류 발생)

```bash
# 빌드
$ make
출력 ▶ gcc -Wall -Wextra -std=c11 -c main.c
출력 ▶ gcc -Wall -Wextra -std=c11 -c math_util.c
출력 ▶ gcc main.o math_util.o -o calc

# 실행
$ ./calc
출력 ▶ 3 + 4 = 7

# 다시 make → 변경이 없으면 재빌드 안 함
$ make
출력 ▶ make: 'calc' is up to date.

# 생성물 정리
$ make clean
```

**Makefile 핵심 문법**

```makefile
목표(target): 의존성(prerequisites)
	실행할 명령          ← 반드시 Tab 들여쓰기
```

- `목표` 가 `의존성` 보다 오래되었을 때만 명령을 실행 → **바뀐 부분만 다시 빌드**
- `$(변수명)` 으로 변수 사용

> ✅ **체크포인트 6**
> `make` → `./calc` → `make clean` 이 순서대로 동작하면 통과입니다.

---

## 실습 7 · 간단한 응용 예제

배운 흐름으로 작은 프로그램을 직접 만들어 봅니다.

### 7-1. 사용자 입력 받기 (scanf)

```bash
$ nano input.c
```

```c
#include <stdio.h>

int main(void) {
    int num;
    printf("정수를 입력하세요: ");
    scanf("%d", &num);
    printf("입력한 수의 제곱 = %d\n", num * num);
    return 0;
}
```

```bash
$ gcc -Wall input.c -o input
$ ./input
출력 ▶ 정수를 입력하세요: 5
출력 ▶ 입력한 수의 제곱 = 25
```

### 7-2. 반복문 (for)

```bash
$ nano loop.c
```

```c
#include <stdio.h>

int main(void) {
    for (int i = 1; i <= 5; i++) {
        printf("카운트 %d\n", i);
    }
    return 0;
}
```

```bash
$ gcc -Wall loop.c -o loop
$ ./loop
출력 ▶ 카운트 1
출력 ▶ 카운트 2
출력 ▶ 카운트 3
출력 ▶ 카운트 4
출력 ▶ 카운트 5
```

> ✅ **체크포인트 7**
> 두 프로그램이 의도대로 동작하면 통과입니다.

---

## 트러블슈팅 — 컴파일 에러 읽는 법

에러 메시지에는 **`파일명:줄번호:열번호: error: 내용`** 형식으로 위치가 표시됩니다. 당황하지 말고 줄번호부터 확인하세요.

| 에러 메시지 | 원인 | 해결 |
|---|---|---|
| `expected ';' before ...` | 세미콜론 `;` 빠짐 | 해당 줄 끝에 `;` 추가 |
| `undefined reference to 'add'` | 함수 정의 파일을 링크 안 함 | 컴파일 명령에 `math_util.c`(또는 `.o`) 포함 |
| `'xxx' undeclared` | 변수/함수 선언 안 됨 | 변수 선언 또는 `#include` 확인 |
| `implicit declaration of function` | 헤더 누락 | 해당 함수의 `#include` 추가 |
| `fatal error: xxx.h: No such file` | 헤더 파일 경로 오류 | 파일명/경로 확인, `"파일.h"` 위치 점검 |
| `Permission denied` (실행 시) | 실행 권한 없음 | `chmod +x 파일명` |
| Makefile `missing separator` | 명령을 스페이스로 들여씀 | **Tab**으로 다시 들여쓰기 |

> 💡 **에러는 위에서부터** 하나씩 해결하세요. 첫 에러를 고치면 그 아래 에러가 연쇄적으로 사라지는 경우가 많습니다.

---

## 최종 점검 체크리스트

- [ ] `gcc --version` 으로 컴파일러 확인
- [ ] `hello.c` 작성 → 컴파일 → `./hello` 실행 성공
- [ ] `-Wall` 옵션으로 경고 확인
- [ ] 컴파일 4단계(`-E`, `-S`, `-c`, 링크) 산출물 확인
- [ ] 여러 파일(`main.c` + `math_util.c`) 분리 컴파일 성공
- [ ] `Makefile` 작성 후 `make` / `make clean` 동작
- [ ] `scanf` 입력 + `for` 반복문 예제 실행

---

## 실습 과제 (제출)

> **제출물**: 소스 코드 + 컴파일/실행 터미널 캡처

1. **계산기 프로그램**
   두 정수를 입력받아 **사칙연산(+, −, ×, ÷)** 결과를 모두 출력하는 `calculator.c` 를 작성하고,
   `gcc -Wall` 로 컴파일해 실행 결과를 캡처하세요. (0으로 나누기 예외 처리 시 가산점)

2. **모듈 분리 + Make**
   1번의 사칙연산을 `calc_util.c` / `calc_util.h` 로 분리하고, `main.c` 에서 호출하도록 구성한 뒤
   **`Makefile` 로 빌드**하여 `make` 로 컴파일되는 것을 캡처하세요.

3. **에러 분석 보고서 (자유 양식, 반쪽)**
   실습 중 마주친 컴파일 에러 1가지를 골라
   - 에러 메시지 원문
   - 원인 분석
   - 해결 방법
   을 정리해 제출하세요.

---

### 다음 시간 예고

> **GPIO 제어와 C** — 라즈베리파이의 GPIO 핀을 C로 제어하며, 지금 익힌 빌드/실행 흐름을 실제 하드웨어 제어에 적용합니다.

---
*Robot Platform · 임베디드 리눅스 과정 · 실습 자료*
