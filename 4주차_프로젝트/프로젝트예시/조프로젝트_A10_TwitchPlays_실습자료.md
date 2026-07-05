# 🎮 조 프로젝트 A10 — 협동 미로 탈출 "Twitch Plays TurtleBot"
## 5일 40시간 팀 프로젝트 과제 명세서 🔴 상급 (Plan B 필수)

> 공통 사항: rosbridge(wss) 준비와 인증서 승인은 1일차 실습 문서 §3~§6,
> 운영·제출 규정과 채점 루브릭(100점)은 「5일 조 프로젝트 운영 가이드」를 따릅니다.

---

## 1. 프로젝트 개요

### 1.1 시나리오

여러 명(3인 이상)이 각자 폰으로 투표 페이지에 접속해 전진/후진/좌/우/
정지에 투표합니다. 1초마다 다수결이 집계되어 로봇이 그 방향으로
움직이고, 관중 화면에는 실시간 득표 현황과 로봇 시점(FPV)이 표시됩니다.
목표는 제한 시간 내 미로(장애물 코스) 탈출. 로봇은 다수결과 무관하게
초음파로 벽 충돌만은 스스로 막습니다 — **민주주의 위에 안전이 있다**는
설계를 배웁니다.

### 1.2 학습 목표

1. rosbridge에 **다중 클라이언트**가 동시 발행하는 시스템을 설계할 수 있다.
2. 시간창 기반 집계(1초 다수결)와 1인 1표 처리(최신 표 우선)를 구현할 수 있다.
3. 사용자 명령보다 상위의 안전 오버라이드 계층을 구현할 수 있다.
4. 다수 사용자 부하에서의 메시지 유실·지연을 관찰하고 대응할 수 있다.

### 1.3 시스템 구조

```
〔투표 폰 ×N〕 vote.html (voter_id 자동 부여)
   │ /vote (JSON, 투표 시 엣지, N명 동시)
   ▼
  wss ──── rosbridge_server ───▶ 〔관중 화면〕 live.html (/vote_stats 구독 + FPV)
   │
   ▼
〔Pi〕 vote_arbiter (1초 창 다수결) ──/cmd_arbitrated(1Hz)──▶ safe_driver
                                          │                      │
        초음파 obstacle_node ──/obstacle_dist(연속)──────────────┤
                                          ▼                      ▼
                                   LCD(현재 명령 표시)     /cmd_vel (10Hz 연속)
```

### 1.4 조원 역할 (5~6인)

| 역할 | 담당 | 핵심 산출물 |
|---|---|---|
| 🌐 웹 A | 투표 페이지 (voter_id·쿨다운) | vote.html |
| 🌐 웹 B | 관중 라이브 화면 (득표 그래프·FPV) | live.html |
| 🤖 ROS A | vote_arbiter (집계) | 중재 노드 + 집계 정책 문서 |
| 🤖 ROS B | safe_driver (실행+오버라이드) | 실행 노드 |
| 🔩 HW | 초음파 노드, LCD, 미로 코스 제작 | 노드 2종 + 코스 도면 |
| 🔗 통합·QA (6인) | 인터페이스·부하 테스트 | INTERFACE.md, TEST.md |

### 1.5 Plan B (Day 1 설계 리뷰 시 함께 제출 — 🔴 주제 의무)

다중 접속이 불안정하면: 참가자를 **3인 고정 + 투표 창 2초**로 축소.
FPV가 어려우면: 관중 화면에서 FPV를 빼고 위에서 찍는 고정 캠으로 대체.
(투표→집계→주행의 핵심 고리는 유지)

---

## 2. 기능 요구사항

### Must

| ID | 요구사항 | 검증 방법 |
|---|---|---|
| M1 | 3인 이상 동시 투표 (폰 3대+) | 동시 접속 시연 |
| M2 | 1초 창 다수결 집계, 1인 1표(최신 표 우선) | 한 명이 창 내 2번 눌러도 1표 |
| M3 | 동점·무투표 → 정지 | 의도적 동점 시연 |
| M4 | 득표 현황 실시간 표시 (관중 화면) | 투표와 그래프 동기 |
| M5 | 초음파 20cm 이내 전방 장애물 → 전진 다수결 무시(정지) | 벽 앞 전진 몰표 테스트 |
| M6 | 확정 명령 소실 2초 → 정지 (arbiter 다운 대비) | arbiter 강제 종료 테스트 |
| M7 | 미로 탈출 완주 (제한 시간 내 1회 이상) | 시연 영상 |
| M8 | 안전장치 3종 | 시연 필수 장면 |

### Should

| ID | 요구사항 |
|---|---|
| S1 | 투표 쿨다운 (1인당 창마다 1회 UI 제한 + 서버 측 최신표 처리 이중화) |
| S2 | 참여자 수·명령 이력 로그 (라운드 리플레이용 기록) |
| S3 | LCD에 현재 확정 명령 표시 |

### Could

| ID | 요구사항 |
|---|---|
| C1 | 팀전 모드 (두 팀 득표 가중 대결) |
| C2 | 골 지점 QR 인식 → 자동 완주 판정 + 기록 측정 |
| C3 | 방해 요소 (특정 칸에서 조작 반전 이벤트) |

---

## 3. 토픽 인터페이스 정의서 (INTERFACE.md 초안)

| 토픽명 | 메시지 타입 | 발행자 | 구독자 | 주기 | 성격 | QoS |
|---|---|---|---|---|---|---|
| /vote | std_msgs/msg/String (JSON) | 투표 폰 ×N | vote_arbiter | 투표 시 | 엣지(다중) | RELIABLE |
| /cmd_arbitrated | std_msgs/msg/String | vote_arbiter | safe_driver | 1Hz | 주기 확정 | RELIABLE |
| /vote_stats | std_msgs/msg/String (JSON) | vote_arbiter | 관중 화면 | 1Hz | **연속** | RELIABLE |
| /obstacle_dist | std_msgs/msg/Float32 | obstacle_node | safe_driver | 10Hz | **연속** | RELIABLE |
| /cmd_vel | geometry_msgs/msg/Twist | safe_driver | 터틀봇 | 10Hz | **연속** | RELIABLE |
| /lcd_text | std_msgs/msg/String | safe_driver | lcd_node | 명령 변화 시 | 엣지 | RELIABLE |

**투표 JSON**: `{"voter": "phone-3f2a", "choice": "forward"}`
(voter는 페이지 접속 시 랜덤 생성해 localStorage 유지)

> ⚠️ `/vote`는 이 과정 유일의 **다대일(N:1) 토픽**입니다. rosbridge는
> 클라이언트마다 독립 WebSocket 연결이므로 동시 발행이 가능하지만,
> N이 커질수록 유실·지연이 생깁니다. 부하 테스트(3/5/10명)가 필수입니다.

---

## 4. 구현 가이드

### 4.1 🌐 투표 페이지 (vote.html)

```javascript
// voter_id: 첫 접속 시 생성, localStorage 보존
let voter = localStorage.getItem('voter') ||
  ('phone-' + Math.random().toString(16).slice(2, 6));
localStorage.setItem('voter', voter);

function vote(choice) {
  voteTopic.publish(new ROSLIB.Message({
    data: JSON.stringify({ voter, choice }) }));
  lockButtons(1000);          // 쿨다운 UI (서버도 최신표만 반영하므로 이중 안전)
}
```

요구 UI: 버튼 5개(⬆⬇⬅➡⏹), 내 마지막 표 표시, 쿨다운 표시.

### 4.2 🌐 관중 화면 (live.html)

`/vote_stats` 구독 → 막대그래프(선택지별 득표)·참여자 수·확정 명령
강조. FPV는 A2와 동일하게 로봇 거치 폰 화면 미러링으로 해결(간단한
방법 우선, WebRTC는 Could).

### 4.3 🤖 vote_arbiter.py (py_compile 검증 완료)

```python
#!/usr/bin/env python3
"""vote_arbiter: 다중 클라이언트 투표 → 1초 창 다수결 확정"""
import json, time
from collections import Counter
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

WINDOW = 1.0
VALID = ('forward', 'back', 'left', 'right', 'stop')


class VoteArbiter(Node):
    def __init__(self):
        super().__init__('vote_arbiter')
        self.votes = []      # (ts, voter_id, choice)
        self.sub = self.create_subscription(String, '/vote', self.on_vote, 50)
        self.pub_cmd = self.create_publisher(String, '/cmd_arbitrated', 10)
        self.pub_stats = self.create_publisher(String, '/vote_stats', 10)
        self.timer = self.create_timer(WINDOW, self.decide)
        self.get_logger().info('vote_arbiter 시작')

    def on_vote(self, msg):
        """{"voter":"phone-3f2a","choice":"forward"} — 창 내 1인 1표(최신 우선)"""
        try:
            v = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        if v.get('choice') not in VALID:
            return
        self.votes.append((time.time(), v.get('voter', '?'), v['choice']))

    def decide(self):
        now = time.time()
        window = [(t, who, c) for (t, who, c) in self.votes if now - t <= WINDOW]
        self.votes = window
        latest = {}                     # 1인 1표: 같은 voter는 최신 표만
        for t, who, c in window:
            latest[who] = c
        counts = Counter(latest.values())
        if not counts:
            choice = 'stop'             # 무투표 → 정지
        else:
            top = counts.most_common()
            if len(top) > 1 and top[0][1] == top[1][1]:
                choice = 'stop'         # 동점 → 정지 (안전 우선)
            else:
                choice = top[0][0]
        cmd = String(); cmd.data = choice
        self.pub_cmd.publish(cmd)       # 1초 주기 확정 명령
        stats = String()
        stats.data = json.dumps({'counts': dict(counts),
                                 'voters': len(latest), 'winner': choice})
        self.pub_stats.publish(stats)


def main():
    rclpy.init()
    node = VoteArbiter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 4.4 🤖 safe_driver.py (py_compile 검증 완료)

```python
#!/usr/bin/env python3
"""safe_driver: 확정 명령 실행 + 초음파 충돌 방지 오버라이드"""
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float32
from geometry_msgs.msg import Twist

CMD_MAP = {'forward': (0.10, 0.0), 'back': (-0.10, 0.0),
           'left': (0.0, 0.5), 'right': (0.0, -0.5), 'stop': (0.0, 0.0)}
OBSTACLE_M = 0.20      # 20cm 이내 전방 장애물 → 전진 차단
CMD_TIMEOUT = 2.0      # 확정 명령 소실 → 정지


class SafeDriver(Node):
    def __init__(self):
        super().__init__('safe_driver')
        self.sub_cmd = self.create_subscription(
            String, '/cmd_arbitrated', self.on_cmd, 10)
        self.sub_dist = self.create_subscription(
            Float32, '/obstacle_dist', self.on_dist, 10)
        self.pub_vel = self.create_publisher(Twist, '/cmd_vel', 10)
        self.current = 'stop'
        self.last_cmd = 0.0
        self.dist = 999.0
        self.timer = self.create_timer(0.1, self.tick)   # 10Hz 연속
        self.get_logger().info('safe_driver 시작')

    def on_cmd(self, msg):
        if msg.data in CMD_MAP:
            self.current = msg.data
            self.last_cmd = time.time()

    def on_dist(self, msg):
        self.dist = float(msg.data)

    def tick(self):
        cmd = Twist()
        alive = (time.time() - self.last_cmd) < CMD_TIMEOUT
        choice = self.current if alive else 'stop'
        if choice == 'forward' and self.dist < OBSTACLE_M:
            choice = 'stop'            # 안전 오버라이드: 다수결보다 우선
        lx, az = CMD_MAP[choice]
        cmd.linear.x, cmd.angular.z = lx, az
        self.pub_vel.publish(cmd)


def main():
    rclpy.init()
    node = SafeDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 4.5 🔩 초음파 / LCD / 미로 코스

- obstacle_node: 전방 초음파 거리 → `/obstacle_dist` 10Hz (Week 2 초음파
  실습 + 발행 추가).
- lcd_node: A1 재사용, `/lcd_text` 발행은 safe_driver 명령 변화 시 —
  **조가 추가**(S3, 의도된 미구현).
- 미로: 박스·책으로 1.5m×2m 코스, 통로 폭 = 로봇 폭 + 30cm 이상,
  직각 코너 2개 이상. 코스 도면(치수 포함)이 HW 산출물.

> ⚠️ **스타터 코드의 알려진 한계(조가 해결할 것)**
> ① voter_id를 조작하면 **한 명이 여러 표**를 만들 수 있습니다(스푸핑) —
> 완벽한 방지는 어렵지만, 접속자 목록 표시·비정상 빈도 감지 같은 완화책을
> 논의해 보고서에 서술하세요(보안 사고 실습). ② 동점=정지 정책은 안전하지만
> **교착**(2:2 반복)을 만들 수 있습니다 — 재투표 안내, 직전 명령 유지 등
> 대안의 트레이드오프를 토론하고 선택 근거를 남기세요.
> ③ 1초 창과 투표 타이밍이 어긋나면 표가 다음 창으로 넘어갑니다 —
> 관중 화면에 창 시작/마감 카운트다운을 표시하면 체감이 크게 좋아집니다.

---

## 5. 일차별 마일스톤

| Day | 마일스톤 (18:00 기준) |
|---|---|
| 1 | 인터페이스 확정, 미로 도면, 집계 정책 문서(동점·무투표·1인1표), **Plan B 문서화** |
| 2 | ①투표 페이지 발행 ②arbiter 집계(topic echo 검증) ③safe_driver 고정 명령 실행 ④초음파 발행 ⑤라이브 더미 그래프 |
| 3 | ★ **폰 2대 투표 → 집계 → 주행 E2E** + 오버라이드 검증 (벽 앞 전진 몰표) |
| 4 | 5명+ 부하 테스트 → 유실률 기록 → 미로 완주 연습 3회+ → 리허설 |
| 5 | 시연·발표·회고 (시연 시 타 조 전원을 관중 투표에 참여시킬 것 — 강사 포함) |

> ⚠️ Day 3 승부처: 2대로 전체 고리를 뚫는 것. 인원 확장은 Day 4의
> 부하 테스트 문제이지 아키텍처 문제가 아니게 만들어야 합니다.

---

## 6. 평가 (기능 40점 세부)

| 항목 | 배점 |
|---|---|
| M1~M7 | 25 |
| Should/Could | 10 (S2 로그·부하 테스트 기록은 3점 가중) |
| 안전장치 3종 (M8) | 5 |

**시연 영상 필수 장면**: ① 3인+ 동시 투표 → 득표 그래프 → 주행 (한 화면)
② 의도적 동점 → 정지 ③ 벽 앞 전진 몰표 → 오버라이드 정지 ④ 미로 완주
⑤ arbiter 강제 종료 → 2초 내 정지

---

## 7. 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| 특정 폰 표가 집계 안 됨 | 해당 폰 인증서 미승인/연결 끊김 | 폰별 https://IP:9090 승인, 연결 상태 UI 표시 |
| 한 명이 표 2개로 집계 | localStorage 초기화로 voter 재발급 | 알려진 한계 ① — 완화책 논의 |
| 2:2 교착으로 진행 불가 | 동점=정지 정책 | 알려진 한계 ② — 정책 토론·개선 |
| 투표했는데 다음 창에 반영 | 창 경계 타이밍 | 카운트다운 표시 (한계 ③) |
| 인원 늘리자 지연 급증 | Wi-Fi/rosbridge 부하 | 부하 테스트 기록, stats 발행 축소, 공유기 점검 |
| 후진으로 벽에 부딪힘 | 오버라이드가 전방만 | 후방 초음파 추가(C 수준) 또는 후진 속도 하향 |
| 로봇이 1초마다 덜컥거림 | 명령이 1Hz로 바뀌는 구조적 특성 | safe_driver에서 가감속 보간(고급) 또는 그대로 두고 게임성으로 수용 |
| arbiter 죽었는데 로봇 계속 감 | CMD_TIMEOUT 미동작 | M6 테스트 재확인 (스타터에 구현됨 — 값 확인) |
| stats 그래프 렉 | 1Hz 초과 렌더 | 수신 시에만 렌더, DOM 재사용 |

---

## 8. 최종 체크리스트

- [ ] 집계 정책 문서(1인1표·동점·무투표·스푸핑 완화)가 보고서에 있다.
- [ ] 부하 테스트 기록(3/5/N명, 유실·지연)이 TEST.md에 있다.
- [ ] 오버라이드·타임아웃이 시연 영상으로 증명된다.
- [ ] 미로 도면(치수)과 완주 기록이 있다.
- [ ] Plan B 문서가 PLAN.md에 있다 (전환 여부 무관).
- [ ] `N조_TwitchPlays.tar.gz` → `tar tzf` 검증 → jikim@imguru.co.kr

---

## 📌 한 장 요약 (복붙용)

```
■ 구조: 투표폰×N(/vote 엣지) → vote_arbiter(1초 창 다수결, 1인1표 최신 우선,
       동점·무투표=정지) → /cmd_arbitrated(1Hz) → safe_driver
       (+/obstacle_dist 연속, 전진 차단 오버라이드, 2초 타임아웃) → /cmd_vel 연속
■ Must: 3인+ 동시 투표 / 다수결 / 동점 정지 / 실시간 득표 / 초음파 오버라이드 /
        명령 소실 정지 / 미로 완주 / 안전장치 3종
■ 핵심 논의 과제: voter 스푸핑 완화, 동점 교착 정책 (근거 서술)
■ Day3 승부처: 폰 2대로 전체 고리 완성 → Day4는 부하와 완주 연습
■ 제출: N조_TwitchPlays.tar.gz → jikim@imguru.co.kr
```
