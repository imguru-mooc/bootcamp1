# 📦 조 프로젝트 A5 — 창고 물류 AGV 시스템
## 5일 40시간 팀 프로젝트 과제 명세서

> 공통 사항: rosbridge(wss) 준비와 인증서 승인은 1일차 실습 문서 §3~§6,
> 운영·제출 규정과 채점 루브릭(100점)은 「5일 조 프로젝트 운영 가이드」를 따릅니다.

---

## 1. 프로젝트 개요

### 1.1 시나리오

관리자가 웹앱에서 운송 작업(A 스테이션 → C 스테이션)을 등록하면 작업
큐에 쌓입니다. AGV(터틀봇)는 로봇 거치 폰으로 바닥/벽면의 스테이션 QR을
인식하며 이동해, 출발지에서 스테퍼 리프트를 올려 적재하고 목적지에서
내려 하역합니다. LCD에는 현재 작업이, 대시보드에는 작업 큐와 진행
상태(대기/이동중/완료)가 실시간 표시됩니다.

### 1.2 학습 목표

1. 작업 큐 스케줄러와 실행기(driver)를 분리한 2계층 구조를 설계할 수 있다.
2. QR 랜드마크 기반 이동이라는 위치 인식의 기초를 구현할 수 있다.
3. 작업 상태(대기→이동중→완료)의 생애주기를 추적할 수 있다.
4. 이동(연속) / 리프트·LCD(엣지) 명령을 하나의 실행 흐름에서 조합할 수 있다.

### 1.3 시스템 구조

```
〔관리자 폰/PC〕 작업 등록 + 큐 대시보드
   │ /task (엣지)                  ▲ /task_state (엣지)
   ▼                               │
  wss ──── rosbridge_server ───────┘
   │
   ▼
〔Pi〕 task_scheduler ──/task_goal──▶ station_driver ──/cmd_vel(연속)──▶ 터틀봇
                                        │  ▲                 │
                              /lift_cmd │  │ /lift_done      │ /lcd_text
                                        ▼  │                 ▼
                                    lift_node(스테퍼)      LCD
   ▲ /station_seen (엣지)
〔로봇 거치 폰〕 스테이션 QR 스캐너 웹앱
```

### 1.4 조원 역할 (5~6인)

| 역할 | 담당 | 핵심 산출물 |
|---|---|---|
| 🌐 웹 | 작업 등록 + 큐 대시보드 | dashboard.html |
| 🧠 AI | 스테이션 QR 스캐너 (주행 중 인식) | scanner.html + 속도별 인식률 표 |
| 🤖 ROS A | task_scheduler | 스케줄러 노드 |
| 🤖 ROS B | station_driver 상태머신 | 실행 노드 + 상태 전이도 |
| 🔩 HW | lift_node(스테퍼), lcd_node, 스테이션 제작 | 노드 2종 + 코스 |
| 🔗 통합·QA (6인) | 인터페이스·테스트 | INTERFACE.md, TEST.md |

---

## 2. 기능 요구사항

### Must

| ID | 요구사항 | 검증 방법 |
|---|---|---|
| M1 | 웹에서 작업 등록(src→dst) → 큐 표시 | 작업 3건 등록 |
| M2 | FIFO 순차 처리 (이동 중 신규 작업은 대기) | 연속 2작업 자동 처리 |
| M3 | 스테이션 QR 인식으로 정지 위치 결정 (3개 스테이션) | 정지 오차 ±20cm |
| M4 | 출발지 리프트 UP, 목적지 리프트 DOWN | 스테퍼 정해진 스텝 수 |
| M5 | LCD에 현재 작업 표시, 대시보드에 상태 전이 표시 | 대기→이동중→완료 |
| M6 | 안전장치 3종 | 시연 필수 장면 |

### Should

| ID | 요구사항 |
|---|---|
| S1 | 우선순위 작업 (긴급 등록 시 큐 맨 앞으로) |
| S2 | QR 미인식 타임아웃 (일정 시간 스테이션 미발견 → 정지 + 대시보드 경고) |
| S3 | 작업 취소 (대기 중 작업만) |

### Could

| ID | 요구사항 |
|---|---|
| C1 | 작업 통계 (건수, 평균 소요 시간) |
| C2 | 초음파 장애물 일시정지 후 재개 |
| C3 | 복수 적재 (경유 스테이션 2곳 순회) |

---

## 3. 토픽 인터페이스 정의서 (INTERFACE.md 초안)

| 토픽명 | 메시지 타입 | 발행자 | 구독자 | 주기 | 성격 | QoS |
|---|---|---|---|---|---|---|
| /task | std_msgs/msg/String (JSON) | 웹앱 | task_scheduler | 등록 시 | 엣지 | RELIABLE |
| /task_state | std_msgs/msg/String (JSON) | task_scheduler | 대시보드 | 변화 시 | 엣지 | RELIABLE |
| /task_goal | std_msgs/msg/String (JSON) | task_scheduler | station_driver | 배정 시 | 엣지 | RELIABLE |
| /station_seen | std_msgs/msg/String (스테이션ID) | QR 스캐너 | station_driver | 인식 시 | 엣지 | RELIABLE |
| /cmd_vel | geometry_msgs/msg/Twist | station_driver | 터틀봇 | 10Hz | **연속** | RELIABLE |
| /lift_cmd | std_msgs/msg/String ("up"/"down") | station_driver | lift_node | 적·하역 시 | 엣지 | RELIABLE |
| /lift_done | std_msgs/msg/String | lift_node | station_driver | 완료 시 | 엣지 | RELIABLE |
| /task_done | std_msgs/msg/String (task_id) | station_driver | task_scheduler | 완료 시 | 엣지 | RELIABLE |
| /lcd_text | std_msgs/msg/String | station_driver | lcd_node | 변화 시 | 엣지 | RELIABLE |

**작업 JSON**: `{"task_id": "T-1720240512", "src": "A", "dst": "C"}`

> ⚠️ `/lift_cmd`→`/lift_done`은 **요청-완료 페어**입니다. driver는
> `lift_done`을 받기 전까지 이동을 재개하면 안 됩니다(적재 중 출발 =
> 화물 낙하). 이런 핸드셰이크 패턴은 실무 AGV의 기본입니다.

---

## 4. 구현 가이드

### 4.1 🧠 스테이션 QR 스캐너 (scanner.html)

A4의 QR 인식과 동일 패턴이되, **주행 중 인식**이라 조건이 다릅니다.
인식 주기를 200ms로 올리고, 같은 스테이션 연속 인식은 1회만 발행하세요.
AI 담당의 핵심 실험: 주행 속도(0.05/0.08/0.12 m/s)별 인식 성공률 표 —
이 표가 CRUISE 속도 결정의 근거가 되고 보고서 점수가 됩니다.

### 4.2 🤖 task_scheduler.py (py_compile 검증 완료)

```python
#!/usr/bin/env python3
"""task_scheduler: 운송 작업 큐 관리 (FIFO, 우선순위 확장 여지)"""
import json
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class TaskScheduler(Node):
    def __init__(self):
        super().__init__('task_scheduler')
        self.queue = []
        self.current = None
        self.sub_task = self.create_subscription(String, '/task', self.on_task, 10)
        self.sub_done = self.create_subscription(String, '/task_done', self.on_done, 10)
        self.pub_goal = self.create_publisher(String, '/task_goal', 10)
        self.pub_state = self.create_publisher(String, '/task_state', 10)
        self.get_logger().info('task_scheduler 시작')

    def on_task(self, msg):
        """웹 작업 등록: {"task_id":"...","src":"A","dst":"C"}"""
        try:
            task = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        task['status'] = '대기'
        self.queue.append(task)
        self.broadcast()
        self.dispatch()

    def on_done(self, msg):
        if self.current and self.current['task_id'] == msg.data:
            self.current['status'] = '완료'
            self.broadcast()
            self.current = None
            self.dispatch()

    def dispatch(self):
        if self.current is not None or not self.queue:
            return
        self.current = self.queue.pop(0)
        self.current['status'] = '이동중'
        goal = String()
        goal.data = json.dumps(self.current, ensure_ascii=False)
        self.pub_goal.publish(goal)
        self.broadcast()

    def broadcast(self):
        msg = String()
        msg.data = json.dumps({'current': self.current, 'queue': self.queue},
                              ensure_ascii=False)
        self.pub_state.publish(msg)


def main():
    rclpy.init()
    node = TaskScheduler()
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

### 4.3 🤖 station_driver.py (py_compile 검증 완료)

```python
#!/usr/bin/env python3
"""station_driver: QR 스테이션 인식 기반 이동 + 리프트 연동
   작업 흐름: src 스테이션까지 전진 → 리프트 UP → dst까지 전진 → 리프트 DOWN"""
import json
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist

CRUISE = 0.08          # 순항 속도 (m/s)


class StationDriver(Node):
    def __init__(self):
        super().__init__('station_driver')
        self.sub_goal = self.create_subscription(String, '/task_goal', self.on_goal, 10)
        self.sub_seen = self.create_subscription(String, '/station_seen', self.on_seen, 10)
        self.sub_lift = self.create_subscription(String, '/lift_done', self.on_lift, 10)
        self.pub_vel = self.create_publisher(Twist, '/cmd_vel', 10)
        self.pub_lift = self.create_publisher(String, '/lift_cmd', 10)
        self.pub_done = self.create_publisher(String, '/task_done', 10)
        self.task = None
        self.phase = 'IDLE'    # IDLE→TO_SRC→LOAD→TO_DST→UNLOAD
        self.timer = self.create_timer(0.1, self.tick)   # 10Hz 연속
        self.get_logger().info('station_driver 시작')

    def on_goal(self, msg):
        self.task = json.loads(msg.data)
        self.phase = 'TO_SRC'
        self.get_logger().info(f"작업 시작: {self.task['src']}→{self.task['dst']}")

    def on_seen(self, msg):
        """로봇 거치 폰의 QR 인식 결과 (스테이션 ID, 엣지)"""
        if not self.task:
            return
        if self.phase == 'TO_SRC' and msg.data == self.task['src']:
            self.phase = 'LOAD'
            self.send_lift('up')
        elif self.phase == 'TO_DST' and msg.data == self.task['dst']:
            self.phase = 'UNLOAD'
            self.send_lift('down')

    def on_lift(self, msg):
        if self.phase == 'LOAD':
            self.phase = 'TO_DST'
        elif self.phase == 'UNLOAD':
            done = String()
            done.data = self.task['task_id']
            self.pub_done.publish(done)
            self.task = None
            self.phase = 'IDLE'

    def send_lift(self, direction):
        msg = String()
        msg.data = direction
        self.pub_lift.publish(msg)     # 엣지

    def tick(self):
        cmd = Twist()
        if self.phase in ('TO_SRC', 'TO_DST'):
            cmd.linear.x = CRUISE      # 이동 중에만 전진
        self.pub_vel.publish(cmd)      # 그 외 정지 명령 연속 발행


def main():
    rclpy.init()
    node = StationDriver()
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

### 4.4 🔩 lift_node / lcd_node / 코스

- **lift_node**: 스테퍼를 정해진 스텝 수(예: ±512)만큼 구동 후 `/lift_done`
  발행. Week 2 스테퍼 실습 코드에 완료 통지만 추가하면 됩니다.
- **lcd_node**: A1과 동일 재사용. LCD 갱신 발행 로직은 driver의 phase
  전이 지점에 **조가 추가**해야 합니다(M5, 의도된 미구현).
- **코스**: 직선 트랙에 A·B·C 스테이션 QR을 40cm 이상 간격으로 부착.
  QR 크기는 8cm 이상 권장(속도별 인식률 표로 근거 제시).

> ⚠️ **스타터 코드의 알려진 한계(조가 해결할 것)**
> ① 단방향 직선 전진만 있어 **C→A처럼 역방향 작업이 불가**합니다 —
> 스테이션 순서를 정의하고 방향 판단(후진 또는 회전)을 추가하세요.
> ② `src == dst`인 작업, 이동 중 새 `/task_goal` 수신(현재 작업 덮어씀)이
> 방어되지 않습니다. ③ LCD 발행이 없습니다(M5). ④ S2 QR 미인식
> 타임아웃이 없어 스테이션을 지나치면 영원히 전진합니다 — 반드시
> 구현하세요(안전 문제).

---

## 5. 일차별 마일스톤

| Day | 마일스톤 (18:00 기준) |
|---|---|
| 1 | 인터페이스 확정, 코스 배치도(스테이션 간격·QR 크기), 상태 전이도 |
| 2 | ①작업 등록→큐 표시 ②주행 중 QR 인식 발행 ③리프트 UP/DOWN+done ④driver 골격 |
| 3 | ★ **단일 작업 E2E**: /task_goal 수동 발행 → src 정지·적재 → dst 하역 (스케줄러 제외) |
| 4 | 스케줄러 연결 + 연속 2작업 + 역방향 + 타임아웃 + 리허설 |
| 5 | 시연·발표·회고 |

> ⚠️ Day 3 승부처: `ros2 topic pub`으로 goal을 직접 넣어 driver 단독
> E2E를 먼저 완성하세요. 스케줄러는 검증된 driver 위에 얹는 것이 순서입니다.

---

## 6. 평가 (기능 40점 세부)

| 항목 | 배점 |
|---|---|
| M1~M5 | 25 (항목당 5) |
| Should/Could | 10 |
| 안전장치 3종 (M6) | 5 |

**시연 영상 필수 장면**: ① 작업 2건 등록 → 큐 표시 ② 1작업 전체 흐름
(적재 장면 클로즈업) ③ 완료 → 다음 작업 자동 출발 ④ QR 가림(미인식) →
타임아웃 정지 + 경고

---

## 7. 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| 스테이션을 지나침 | 속도 대비 인식 주기 부족 | 인식 200ms + CRUISE 하향, 인식률 표 근거 |
| 지나친 뒤 영원히 전진 | 알려진 한계 ④ | S2 타임아웃 구현 (안전 필수) |
| C→A 작업이 안 됨 | 알려진 한계 ① | 역방향 이동 설계 |
| 적재 중 출발해 화물 낙하 | lift_done 대기 미준수 | 핸드셰이크 로직 확인 (§3 ⚠️) |
| 같은 QR로 LOAD가 두 번 트리거 | 정지 중 재인식 | phase 조건으로 이미 방어 — 웹 중복 발행도 1회 제한 |
| 두 번째 작업이 즉시 완료 처리 | task_id 불일치/비교 오류 | `topic echo /task_done`으로 id 확인 |
| 스테퍼가 힘없이 헛돎 | 전원 부족/시퀀스 오류 | 외부 전원, Week 2 스테퍼 실습 배선 재확인 |
| LCD에 아무것도 안 뜸 | 알려진 한계 ③ (발행 미구현) | phase 전이 지점에 /lcd_text 추가 |
| 대시보드 큐가 안 줄어듦 | broadcast 시점 누락 | dispatch/done 양쪽 모두 broadcast 확인 |

---

## 8. 최종 체크리스트

- [ ] 상태 전이도(IDLE→TO_SRC→LOAD→TO_DST→UNLOAD)와 구현이 일치한다.
- [ ] 알려진 한계 ①~④가 해결되고 보고서에 설명되었다.
- [ ] 속도별 QR 인식률 표가 보고서에 있다.
- [ ] 연속 2작업(그중 1건 역방향)이 재부팅 없이 완주된다.
- [ ] `N조_물류AGV.tar.gz` → `tar tzf` 검증 → jikim@imguru.co.kr

---

## 📌 한 장 요약 (복붙용)

```
■ 구조: 웹(/task) → task_scheduler(FIFO) → station_driver(상태머신)
       → /cmd_vel 연속 + QR폰(/station_seen 엣지) + lift_cmd↔lift_done 핸드셰이크
■ Must: 작업 등록·큐 / FIFO / QR 정지(3스테이션) / 리프트 적·하역 /
        LCD·상태 전이 표시 / 안전장치 3종
■ 핵심 과제: 역방향 이동, QR 미인식 타임아웃(안전), LCD 발행 추가
■ Day3 승부처: goal 수동 주입으로 driver 단독 E2E 먼저
■ 제출: N조_물류AGV.tar.gz → jikim@imguru.co.kr
```
