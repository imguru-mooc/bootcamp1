# 자주 쓰는 리눅스 명령어 실습 (Ubuntu 22.04)

**로봇 플랫폼 (Robot Platform) · 임베디드 리눅스 실습 자료**
운영체제: **Ubuntu 22.04 LTS** (데스크톱 PC · 라즈베리파이 4 · Jetson Orin Nano 공통)

> 터미널 명령은 임베디드 리눅스의 **기본 언어**입니다. SSH로 보드에 접속해 파일을 옮기고,
> 프로세스를 확인하고, 권한을 바꾸는 일을 모두 명령으로 합니다.
> 눈으로 읽지 말고 **실습용 폴더에서 직접 입력**하며 손에 익히세요.

---

## 학습 목표

- 파일 시스템을 탐색하고 파일/디렉터리를 자유롭게 다룬다.
- 파일 내용을 다양한 방법으로 확인하고, 원하는 내용을 검색한다.
- 파일 권한과 소유자를 이해하고 변경한다.
- 프로세스와 시스템 자원을 확인하고 관리한다.
- 리다이렉션·파이프로 명령을 조합하는 법을 익힌다.
- 작업 효율을 높이는 단축키와 꿀팁을 활용한다.

---

## 표기 약속 & 실습 준비

```text
$           # 프롬프트 (직접 입력하는 명령)
#           # 주석 — 입력하지 않음
출력 ▶      # 실행 결과 예시
```

먼저 **안전한 실습용 폴더**를 만듭니다. 모든 연습은 이 안에서 진행하니 실수해도 안전합니다.

```bash
$ mkdir -p ~/linux_lab && cd ~/linux_lab
$ pwd
출력 ▶ /home/사용자명/linux_lab
```

> 💡 이후 실습은 별도 안내가 없으면 모두 `~/linux_lab` 안에서 진행합니다.

---

## 1 · 파일 시스템 탐색

| 명령 | 의미 |
|---|---|
| `pwd` | 현재 위치(경로) 출력 (print working directory) |
| `ls` | 디렉터리 내용 목록 |
| `cd` | 디렉터리 이동 (change directory) |
| `tree` | 폴더 구조를 트리로 표시 |

```bash
# 현재 위치 확인
$ pwd

# 목록 보기 (옵션 조합)
$ ls            # 기본 목록
$ ls -l         # 상세 정보(권한/크기/날짜)
$ ls -a         # 숨김 파일(.로 시작)까지
$ ls -lh        # 사람이 읽기 쉬운 크기(KB/MB)
$ ls -al        # 자주 쓰는 조합

# 이동
$ cd /etc       # 절대 경로로 이동
$ cd ~          # 홈 디렉터리로
$ cd ..         # 상위 디렉터리로
$ cd -          # 직전 위치로 되돌아가기
$ cd ~/linux_lab
```

**경로 약어**

| 기호 | 의미 |
|---|---|
| `~` | 내 홈 디렉터리 (`/home/사용자명`) |
| `.` | 현재 디렉터리 |
| `..` | 상위 디렉터리 |
| `/` | 최상위(루트) 디렉터리 |

> 🧪 **실습**: `cd /` → `ls` 로 리눅스 최상위 구조를 보고, `cd ~` 로 돌아오세요.

> ✅ **체크포인트 1**
> `pwd`, `ls -al`, `cd ..` / `cd -` 를 자유롭게 사용할 수 있으면 통과.

---

## 2 · 파일 · 디렉터리 다루기

| 명령 | 의미 |
|---|---|
| `mkdir` | 디렉터리 생성 |
| `touch` | 빈 파일 생성 / 시간 갱신 |
| `cp` | 복사 (copy) |
| `mv` | 이동 / 이름 변경 (move) |
| `rm` | 삭제 (remove) |

```bash
$ cd ~/linux_lab

# 디렉터리 만들기 (-p: 중간 경로까지 한 번에)
$ mkdir test
$ mkdir -p project/src project/docs

# 빈 파일 만들기
$ touch a.txt b.txt c.txt

# 복사
$ cp a.txt copy_a.txt          # 파일 복사
$ cp -r project project_backup # 폴더 통째로 복사(-r)

# 이동 & 이름 변경
$ mv b.txt test/               # test 폴더로 이동
$ mv c.txt renamed.txt         # 이름 변경

# 삭제
$ rm copy_a.txt                # 파일 삭제
$ rm -r project_backup         # 폴더 삭제(-r)
```

> ⚠️ **`rm` 은 휴지통이 없습니다. 삭제 = 즉시 영구 삭제.**
> 특히 **`rm -rf` 는 매우 위험**합니다. 경로를 반드시 두 번 확인하세요.
> 절대 `rm -rf /` 또는 `rm -rf ~` 같은 명령을 실행하지 마세요. (시스템/홈 전체 삭제)
> 안전을 위해 처음엔 `rm -i`(삭제 전 확인) 사용을 권장합니다.

> 🧪 **실습**: `mkdir`로 폴더를 만들고 `touch`로 파일 3개를 만든 뒤, `tree` 로 구조를 확인하세요.

> ✅ **체크포인트 2**
> 디렉터리/파일 생성·복사·이동·삭제를 모두 수행할 수 있으면 통과.

---

## 3 · 파일 내용 보기

먼저 실습용 내용 파일을 만듭니다.

```bash
$ cd ~/linux_lab
$ printf "line1\nline2\nline3\nline4\nline5\n" > sample.txt
```

| 명령 | 용도 |
|---|---|
| `cat` | 파일 전체 출력 |
| `less` | 페이지 단위로 보기 (긴 파일) |
| `head` | 앞부분 보기 (기본 10줄) |
| `tail` | 뒷부분 보기 (기본 10줄) |
| `wc` | 줄/단어/글자 수 세기 |

```bash
$ cat sample.txt          # 전체 출력
$ head -2 sample.txt      # 앞 2줄
$ tail -2 sample.txt      # 뒤 2줄
$ wc -l sample.txt        # 줄 수만
출력 ▶ 5 sample.txt

# less로 보기 (긴 로그 파일에 유용)
$ less /var/log/syslog
# less 안에서: ↑↓ 이동, Space 다음 페이지, /검색어, q 종료

# tail -f : 실시간 로그 모니터링 (로봇/서버 디버깅에 필수)
$ tail -f /var/log/syslog
# 종료: Ctrl + C
```

> 💡 `tail -f` 는 파일에 새 내용이 추가될 때마다 **실시간으로 보여줍니다.** 센서 로그·서버 로그 확인에 매우 유용합니다.

> ✅ **체크포인트 3**
> `cat`, `head`, `tail`, `wc -l` 을 사용할 수 있고 `less`를 `q`로 종료할 수 있으면 통과.

---

## 4 · 검색 (파일 찾기 & 내용 찾기)

| 명령 | 용도 |
|---|---|
| `find` | 조건으로 **파일 찾기** |
| `grep` | 파일 **내용에서 문자열 찾기** |
| `which` | 명령(실행 파일)의 위치 찾기 |

```bash
$ cd ~/linux_lab

# find: 이름으로 파일 찾기
$ find . -name "*.txt"            # 현재 폴더 이하 모든 .txt
$ find . -type d                  # 디렉터리만
$ find . -type f -name "a*"       # a로 시작하는 파일

# grep: 파일 안에서 문자열 찾기
$ grep "line3" sample.txt
출력 ▶ line3
$ grep -n "line" sample.txt       # 줄 번호와 함께(-n)
$ grep -i "LINE" sample.txt       # 대소문자 무시(-i)
$ grep -r "TODO" ~/linux_lab      # 폴더 전체 재귀 검색(-r)

# which: 명령 위치 확인
$ which python3
출력 ▶ /usr/bin/python3
```

> 💡 `grep` 은 파이프와 함께 쓰면 강력합니다.
> ```bash
> $ ls -al | grep ".txt"        # 목록 중 .txt만 걸러내기
> ```

> 🧪 **실습**: `find ~/linux_lab -name "*.txt"` 로 만들어 둔 텍스트 파일을 모두 찾아보세요.

> ✅ **체크포인트 4**
> `find -name`, `grep -n`, `which` 를 사용할 수 있으면 통과.

---

## 5 · 권한 관리

`ls -l` 로 보이는 권한 표기를 이해합니다.

```text
-rwxr-xr--   1 user group  0 Jun 16 10:00 script.sh
│└┬┘└┬┘└┬┘
│ │  │  └─ 기타 사용자(others) 권한
│ │  └──── 그룹(group) 권한
│ └─────── 소유자(user) 권한
└───────── 파일 종류 (- 파일, d 디렉터리, l 링크)
```

| 문자 | 의미 | 숫자 |
|---|---|---|
| `r` | 읽기 (read) | 4 |
| `w` | 쓰기 (write) | 2 |
| `x` | 실행 (execute) | 1 |

```bash
$ cd ~/linux_lab
$ echo 'echo "Hello"' > script.sh

# 현재 권한 확인
$ ls -l script.sh

# 실행 권한 추가 (기호 방식)
$ chmod +x script.sh
$ ./script.sh
출력 ▶ Hello

# 숫자 방식: 755 = rwx(7) r-x(5) r-x(5)
$ chmod 755 script.sh
$ chmod 644 sample.txt    # rw-r--r-- (일반 파일 표준)
```

**자주 쓰는 권한 숫자**

| 숫자 | 권한 | 용도 |
|---|---|---|
| `755` | rwxr-xr-x | 실행 파일/스크립트 |
| `644` | rw-r--r-- | 일반 문서 |
| `600` | rw------- | 개인 키 등 비공개 파일 |

```bash
# 소유자 변경(관리자 권한 필요)
$ sudo chown 사용자명:그룹명 파일명
```

> 💡 `sudo` 는 관리자(root) 권한으로 명령을 실행합니다. 시스템 파일 수정·패키지 설치 시 필요합니다.

> ✅ **체크포인트 5**
> `ls -l` 권한 표기를 읽을 수 있고, `chmod +x` 로 스크립트를 실행할 수 있으면 통과.

---

## 6 · 프로세스 관리

| 명령 | 용도 |
|---|---|
| `ps` | 실행 중인 프로세스 목록 |
| `top` / `htop` | 실시간 자원/프로세스 모니터 |
| `kill` | 프로세스 종료 |
| `&` / `jobs` / `fg` | 백그라운드 실행 관리 |

```bash
# 프로세스 목록
$ ps aux                  # 모든 프로세스 상세
$ ps aux | grep python    # python 관련만 필터링

# 실시간 모니터 (q로 종료)
$ top
$ htop                    # 더 보기 좋음 (sudo apt install htop)

# 프로세스 종료
$ kill 1234               # PID 1234 종료
$ kill -9 1234            # 강제 종료(SIGKILL)
$ pkill python3           # 이름으로 종료
```

**백그라운드 실행**

```bash
# 명령 끝에 & 를 붙이면 백그라운드로 실행
$ sleep 100 &
출력 ▶ [1] 4567        # [작업번호] PID

$ jobs                 # 백그라운드 작업 목록
$ fg %1                # 1번 작업을 다시 앞으로
# (실행 중 Ctrl+Z = 일시정지, bg = 백그라운드 재개)
```

> 💡 로봇 프로그램을 백그라운드로 돌리거나, 멈춘 프로세스를 강제 종료할 때 자주 씁니다.

> ✅ **체크포인트 6**
> `ps aux | grep`, `top`(q 종료), `kill PID` 를 사용할 수 있으면 통과.

---

## 7 · 시스템 정보 확인

| 명령 | 용도 |
|---|---|
| `uname -a` | 커널/아키텍처 정보 |
| `df -h` | 디스크 여유 공간 |
| `du -sh` | 폴더 용량 |
| `free -h` | 메모리 사용량 |
| `lscpu` | CPU 정보 |
| `uptime` | 가동 시간/부하 |

```bash
$ uname -a                # 시스템 전체 정보
$ uname -m                # 아키텍처 (x86_64 / aarch64)
$ df -h                   # 디스크 (-h: 읽기 쉬운 단위)
$ du -sh ~/linux_lab      # 특정 폴더 용량(-s 합계, -h 단위)
$ free -h                 # 메모리
$ lscpu | head -10        # CPU 정보 일부
$ uptime                  # 켜진 시간 + 평균 부하
```

> 💡 〔SBC〕 라즈베리파이/Jetson에서 디스크가 가득 차거나 메모리가 부족할 때 `df -h`·`free -h` 로 먼저 점검합니다.

> ✅ **체크포인트 7**
> `df -h`, `free -h`, `uname -m` 으로 시스템 상태를 확인할 수 있으면 통과.

---

## 8 · 네트워크 명령

| 명령 | 용도 |
|---|---|
| `ip addr` | IP 주소 확인 |
| `ping` | 연결 확인 |
| `ssh` | 원격 접속 |
| `scp` | 원격 파일 복사 |
| `wget` / `curl` | 파일/데이터 다운로드 |

```bash
# 내 IP 주소 확인 (SBC 원격 접속 시 필수)
$ ip addr
$ hostname -I            # IP만 간단히

# 연결 확인 (Ctrl+C로 종료)
$ ping -c 4 8.8.8.8      # 4번만(-c 4) 핑

# 원격 접속 (보드에 SSH 접속)
$ ssh 사용자명@192.168.0.10

# 원격 파일 복사 (PC → 보드)
$ scp myfile.txt 사용자명@192.168.0.10:~/

# 파일 다운로드
$ wget https://example.com/file.zip
$ curl -O https://example.com/file.zip
```

> 💡 임베디드 실습에서 **`ip addr`로 보드 IP 확인 → `ssh`로 접속 → `scp`로 코드 전송** 흐름을 매우 자주 사용합니다.

> ✅ **체크포인트 8**
> `hostname -I` 로 IP를 확인하고 `ping -c 4` 로 연결을 테스트할 수 있으면 통과.

---

## 9 · 패키지 관리 (apt)

```bash
$ sudo apt update                 # 패키지 목록 갱신
$ sudo apt upgrade -y             # 설치된 패키지 업그레이드
$ sudo apt install -y 패키지명    # 설치
$ sudo apt remove 패키지명        # 제거
$ apt search 키워드               # 패키지 검색
$ apt list --installed | grep 키워드   # 설치된 것 중 검색
```

> 💡 `update`(목록 갱신)와 `upgrade`(실제 설치)는 다릅니다. 설치 전 항상 `update` 를 먼저 합니다.

---

## 10 · 압축 & 해제

| 형식 | 압축 | 해제 |
|---|---|---|
| tar.gz | `tar -czvf out.tar.gz 폴더` | `tar -xzvf out.tar.gz` |
| zip | `zip -r out.zip 폴더` | `unzip out.zip` |

```bash
$ cd ~/linux_lab

# tar.gz 압축 (c생성 z압축 v과정표시 f파일명)
$ tar -czvf backup.tar.gz test/

# 해제 (x추출)
$ tar -xzvf backup.tar.gz

# zip (필요 시: sudo apt install zip unzip)
$ zip -r backup.zip test/
$ unzip backup.zip
```

> 💡 옵션 암기 팁: 압축은 **c**reate, 해제는 e**x**tract. `z`(gzip), `v`(verbose), `f`(file)는 공통.

> ✅ **체크포인트 10**
> `tar -czvf` 로 압축하고 `tar -xzvf` 로 해제할 수 있으면 통과.

---

## 11 · 리다이렉션 & 파이프 (조합의 힘) ⭐

명령의 출력을 **파일로 보내거나**, 다른 명령의 **입력으로 연결**할 수 있습니다. 리눅스의 가장 강력한 기능입니다.

| 기호 | 의미 |
|---|---|
| `>` | 출력을 파일로 (덮어쓰기) |
| `>>` | 출력을 파일에 추가 |
| `<` | 파일을 입력으로 |
| `\|` | 앞 명령의 출력을 뒤 명령의 입력으로 (파이프) |
| `&&` | 앞 명령 성공 시 뒤 명령 실행 |

```bash
$ cd ~/linux_lab

# 리다이렉션
$ echo "첫 줄" > log.txt          # 새로 쓰기
$ echo "둘째 줄" >> log.txt       # 이어 쓰기
$ cat log.txt

# 파이프: 명령 연결
$ ls -al | grep ".txt"            # 목록 중 .txt만
$ ps aux | grep python            # 프로세스 중 python만
$ cat /etc/passwd | wc -l         # 줄 수 세기
$ ls | head -3                    # 목록 앞 3개만

# 조합
$ history | grep cd               # 명령 기록 중 cd 들어간 것
$ dmesg | grep -i usb             # 커널 로그 중 USB 관련

# && 연쇄 실행
$ mkdir newdir && cd newdir       # 폴더 만들고 성공하면 이동
```

> 🧪 **실습**: `ls -al | grep ".txt" | wc -l` 로 .txt 파일 개수를 세어 보세요. (파이프 3단 연결)

> ✅ **체크포인트 11**
> `>` / `>>` 로 파일에 출력하고, `|` 로 두 명령 이상을 연결할 수 있으면 통과.

---

## 12 · 작업 효율 꿀팁

### 키보드 단축키 (터미널)

| 단축키 | 동작 |
|---|---|
| `Tab` | 자동 완성 (파일명/명령) |
| `↑` `↓` | 이전/다음 명령 불러오기 |
| `Ctrl + C` | 실행 중인 명령 중단 |
| `Ctrl + L` | 화면 지우기 (= `clear`) |
| `Ctrl + A` / `Ctrl + E` | 줄 맨 앞 / 맨 끝으로 |
| `Ctrl + R` | 명령 기록 검색 |
| `Ctrl + Z` | 현재 작업 일시정지 |

> 💡 **Tab 자동완성**은 가장 강력한 꿀팁입니다. 파일명을 다 치지 말고 앞 글자만 친 뒤 `Tab`을 누르세요. 오타도 줄어듭니다.

### 명령 기록 & 단축어

```bash
$ history                  # 지금까지 입력한 명령 목록
$ history | grep apt       # 기록 중 apt 검색
$ !100                     # 100번 명령 다시 실행
$ !!                       # 직전 명령 다시 실행
$ sudo !!                  # 직전 명령을 sudo로 다시 실행
```

```bash
# alias: 자주 쓰는 긴 명령을 짧게 (~/.bashrc에 추가하면 영구 적용)
$ alias ll='ls -alF'
$ alias ..='cd ..'
```

### 도움말 보기

```bash
$ man ls                   # 매뉴얼(설명서) — q로 종료
$ ls --help                # 간단한 옵션 도움말
$ tldr ls                  # 예제 중심 요약(설치 필요: sudo apt install tldr)
```

> 💡 명령 사용법이 헷갈리면 **`명령 --help`** 또는 **`man 명령`** 을 먼저 보세요. 검색보다 빠를 때가 많습니다.

> ✅ **체크포인트 12**
> Tab 자동완성, `↑`(이전 명령), `Ctrl+R`(기록 검색), `man` 을 사용할 수 있으면 통과.

---

## 핵심 치트시트 (요약)

```text
[ 탐색 ]    pwd  ls -al  cd ..  cd -  tree
[ 파일 ]    mkdir -p  touch  cp -r  mv  rm -i   (rm -rf 주의!)
[ 보기 ]    cat  less  head -n  tail -f  wc -l
[ 검색 ]    find . -name "*.txt"   grep -rn "단어"   which
[ 권한 ]    ls -l   chmod +x   chmod 755   sudo chown
[ 프로세스 ] ps aux | grep  top/htop  kill -9 PID  명령 &
[ 시스템 ]  uname -m  df -h  du -sh  free -h  uptime
[ 네트워크 ] ip addr  ping -c 4  ssh  scp  wget/curl
[ 패키지 ]  sudo apt update && sudo apt install -y 패키지
[ 압축 ]    tar -czvf x.tar.gz 폴더    tar -xzvf x.tar.gz
[ 조합 ]    >  >>  |  &&     예) ls -al | grep .txt | wc -l
[ 꿀팁 ]    Tab 완성   ↑ 이전명령   Ctrl+R 검색   history   man
```

---

## 주의 명령 (실행 금지/조심)

| 명령 | 위험 |
|---|---|
| `rm -rf /` | 시스템 전체 삭제 |
| `rm -rf ~` | 홈 디렉터리 전체 삭제 |
| `chmod -R 777 /` | 시스템 권한 붕괴 |
| `> 중요파일` | 파일 내용을 빈 것으로 덮어씀 |
| `dd` (잘못 사용) | 디스크 통째로 덮어쓰기 |

> ⚠️ 위험한 삭제 전에는 항상 `pwd` 로 **현재 위치**를, `ls` 로 **대상**을 확인하는 습관을 들이세요.

---

## 최종 점검 체크리스트

- [ ] `pwd`·`ls -al`·`cd`로 파일 시스템을 탐색할 수 있다
- [ ] `mkdir`·`cp`·`mv`·`rm`으로 파일을 다룰 수 있다
- [ ] `cat`·`head`·`tail -f`로 파일 내용을 확인할 수 있다
- [ ] `find`·`grep`으로 파일과 내용을 검색할 수 있다
- [ ] `ls -l` 권한을 읽고 `chmod`로 변경할 수 있다
- [ ] `ps`·`top`·`kill`로 프로세스를 관리할 수 있다
- [ ] `df -h`·`free -h`로 시스템 상태를 본다
- [ ] `ip addr`·`ping`·`ssh`로 네트워크를 다룬다
- [ ] `>`·`>>`·`|`로 명령을 조합할 수 있다
- [ ] Tab 완성·`history`·`man`을 활용한다

---

## 실습 과제 (제출)

> **제출물**: 각 문제를 수행한 **명령어 + 결과 터미널 캡처**

1. **파일 정리 미션**
   `~/linux_lab/mission` 폴더를 만들고, 그 안에 `data1.txt` ~ `data5.txt` 를 생성하세요.
   이어서 `.txt` 파일만 모아 `texts` 폴더로 옮기고, `tree` 로 결과 구조를 캡처하세요.

2. **검색 미션**
   `~/linux_lab` 이하에서 이름에 `data` 가 들어간 파일을 모두 찾고(`find`),
   `sample.txt` 안에서 `line` 이 들어간 줄을 줄 번호와 함께 찾으세요(`grep -n`).

3. **파이프 미션**
   `ls -al ~/linux_lab` 결과에서 **`.txt` 파일의 개수**를 파이프로 세어 출력하세요.
   (힌트: `ls | grep | wc -l`)

4. **시스템 보고서 (자유 양식, 반쪽)**
   `uname -a`, `df -h`, `free -h`, `lscpu` 결과를 캡처하고,
   본인 시스템의 **아키텍처·디스크 여유·메모리 크기**를 정리하세요.

---

### 다음 시간 예고

> **쉘 스크립트(Bash) 작성** — 지금까지 배운 명령들을 묶어 자동 실행하는 스크립트를 만듭니다.
> 변수·조건문·반복문으로 반복 작업을 자동화합니다.

---
*Robot Platform · 임베디드 리눅스 과정 · 실습 자료*
