# Day 3 · 과제 솔루션 (액추에이터 제어 + 시각화)

> **대상** Day 3 본문 「액추에이터 제어 + 시각화」 과제 6문항 (기본 2 · 심화 2 · 도전 2)
> **환경** 노트북(Ubuntu 22.04) + 라즈베리파이 4B(Ubuntu 22.04), 양쪽 **ROS 2 Humble** · Freenove 키트
> **전제** Day 3 본문의 노드(`display_hub.py`·`seg_display.py`·`servo_node.py`·`dc_motor_node.py`·`obstacle_guard.py` 등)와 Day 2의 `ultrasonic_range_pub.py`·`adc_sensor_hub.py`가 준비되어 있어야 합니다.
> **실행 위치** 각 코드 상단의 `〔Pi〕`/`〔노트북〕` 표시를 따르며, 솔루션 파일은 `~/ros2_labs/`에 저장합니다.

본문에서 만든 토픽들을 그대로 재사용합니다. 솔루션이 의존하는 토픽과 메시지 타입은 다음과 같습니다.

| 토픽 | 타입 | 출처 |
|---|---|---|
| `/status` | `std_msgs/String` (`ok`/`warn`/`danger`) | 3-1 표시 허브 |
| `/servo_angle` | `std_msgs/Float64` (0~180) | 3-2 서보 |
| `/number` | `std_msgs/Int32` (0~9 표시) | 3-1 7세그먼트 |
| `/pot` | `std_msgs/Float64` (전압 0~3.3 V) | **Day 2** ADC 허브 |
| `/ultrasonic/range` | `sensor_msgs/Range` (m) | **Day 2** 초음파 |
| `/cmd_vel`, `/cmd_vel_in` | `geometry_msgs/Twist` | 3-2·3-4 모터/가드 |

> 💡 모든 코드는 **문법 검증(py_compile)** 과 **예약어 충돌 검사**(`handle`·`context`·`clock`·`executor` 미사용)를 마쳤습니다. 핀 번호·공통 음/양극·I2C 주소·세그먼트 코드 등 **하드웨어 의존 값은 실제 보드에서 확인**하세요.

---

## 기본 1 · 상태 순환 발행 (`/status`)

**핵심** `/status`(String)에 `ok`→`warn`→`danger`를 **1초 간격으로 순환** 발행해, 본문 3-1의 표시 허브(LED·RGB·부저)가 차례로 반응하는지 확인합니다. 타이머 콜백 한 번에 한 상태씩 발행하고 인덱스를 돌립니다.

`~/ros2_labs/sol1_status_cycle.py` (노트북)

```python
#!/usr/bin/env python3
# 〔노트북〕 과제 기본1: /status로 ok→warn→danger를 1초 간격 순환 발행
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class StatusCycle(Node):
    def __init__(self):
        super().__init__('status_cycle')
        self.pub = self.create_publisher(String, 'status', 10)
        self.states = ['ok', 'warn', 'danger']
        self.idx = 0
        self.timer = self.create_timer(1.0, self.tick)   # 1초 간격
        self.get_logger().info('상태 순환 발행 시작 — 1초 간격 ok/warn/danger')

    def tick(self):
        msg = String()
        msg.data = self.states[self.idx]
        self.pub.publish(msg)
        self.get_logger().info(f'발행: {msg.data}')
        self.idx = (self.idx + 1) % len(self.states)

def main(args=None):
    rclpy.init(args=args)
    node = StatusCycle()
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

```bash
# 〔Pi〕 표시 허브 (본문 3-1)
$ python3 ~/ros2_labs/display_hub.py
# 〔노트북〕 상태 순환 발행
$ python3 ~/ros2_labs/sol1_status_cycle.py
```

```text
출력 ▶ (예시)  — 〔노트북〕 status_cycle
[INFO] [status_cycle]: 발행: ok
[INFO] [status_cycle]: 발행: warn
[INFO] [status_cycle]: 발행: danger
[INFO] [status_cycle]: 발행: ok
```

**확인** 1초마다 LED·RGB·부저가 초록 → 노랑(깜빡) → 빨강(부저) 순으로 반복하면 정상입니다.

---

## 기본 2 · 서보 스윕 (`/servo_angle`)

**핵심** `/servo_angle`(Float64)에 각도를 조금씩 올렸다 내렸다 발행해 서보를 **0↔180도로 천천히 왕복**시킵니다. 한 틱마다 일정 각도(step)를 더하고, 양 끝(0·180)에 닿으면 부호를 뒤집어 방향을 바꿉니다.

`~/ros2_labs/sol2_servo_sweep.py` (노트북)

```python
#!/usr/bin/env python3
# 〔노트북〕 과제 기본2: /servo_angle로 0→180→0 왕복(스윕) 발행
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64

class ServoSweep(Node):
    def __init__(self):
        super().__init__('servo_sweep')
        self.pub = self.create_publisher(Float64, 'servo_angle', 10)
        self.angle = 0.0
        self.step = 3.0          # 한 틱당 3도
        self.timer = self.create_timer(0.05, self.tick)   # 0.05초마다 → 한 방향 약 3초
        self.get_logger().info('서보 스윕 시작 — 0↔180도 왕복')

    def tick(self):
        self.angle += self.step
        if self.angle >= 180.0:
            self.angle = 180.0
            self.step = -abs(self.step)       # 끝에 닿으면 방향 반전
        elif self.angle <= 0.0:
            self.angle = 0.0
            self.step = abs(self.step)
        msg = Float64()
        msg.data = self.angle
        self.pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = ServoSweep()
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

```bash
# 〔Pi〕 서보 노드 (본문 3-2)
$ python3 ~/ros2_labs/servo_node.py
# 〔노트북〕 스윕 발행
$ python3 ~/ros2_labs/sol2_servo_sweep.py
```

**확인** 서보가 멈추지 않고 0도에서 180도까지 부드럽게 갔다가 되돌아오면 정상입니다.

> 💡 너무 빠르거나 떨리면 `step`을 줄이거나 타이머 주기(`0.05`)를 늘려 속도를 낮추세요. 본문 3-2의 `servo_node`가 0~180도로 클램프하므로 범위를 벗어나도 안전합니다.

---

## 심화 3 · 가변저항으로 서보 각도 제어 (`/pot` → `/servo_angle`)

**핵심** Day 2 ADC 허브가 발행하는 `/pot`(전압 0~3.3 V)을 구독해, 전압을 **0~180도로 선형 매핑**한 뒤 `/servo_angle`로 발행합니다. 가변저항을 돌리면 서보가 따라 움직입니다. ADC 잡음으로 인한 미세 떨림을 막기 위해 **1도 이상 변했을 때만** 발행합니다.

`~/ros2_labs/sol3_pot_servo.py` (노트북)

```python
#!/usr/bin/env python3
# 〔노트북〕 과제 심화3: /pot(전압 0~3.3V) → 0~180도 매핑 → /servo_angle 발행
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64

V_MIN, V_MAX = 0.0, 3.3      # Day 2 가변저항 전압 범위

class PotToServo(Node):
    def __init__(self):
        super().__init__('pot_to_servo')
        self.pub = self.create_publisher(Float64, 'servo_angle', 10)
        self.sub = self.create_subscription(Float64, 'pot', self.on_pot, 10)
        self.last_angle = None
        self.get_logger().info('가변저항→서보 매핑 시작 — /pot 구독')

    def on_pot(self, msg):
        v = max(V_MIN, min(V_MAX, msg.data))           # 0~3.3V로 클램프
        angle = (v - V_MIN) / (V_MAX - V_MIN) * 180.0  # 0~180도로 선형 매핑
        # 떨림 방지: 1도 이상 바뀔 때만 발행
        if self.last_angle is None or abs(angle - self.last_angle) >= 1.0:
            out = Float64()
            out.data = angle
            self.pub.publish(out)
            self.last_angle = angle
            self.get_logger().info(f'전압 {v:.2f}V → 각도 {angle:.0f}도')

def main(args=None):
    rclpy.init(args=args)
    node = PotToServo()
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

```bash
# 〔Pi〕 ADC 허브 (Day 2) + 서보 노드 (본문 3-2)
$ python3 ~/ros2_labs/adc_sensor_hub.py
$ python3 ~/ros2_labs/servo_node.py
# 〔노트북〕 매핑 노드
$ python3 ~/ros2_labs/sol3_pot_servo.py
```

```text
출력 ▶ (예시)  — 〔노트북〕 pot_to_servo
[INFO] [pot_to_servo]: 전압 0.00V → 각도 0도
[INFO] [pot_to_servo]: 전압 1.65V → 각도 90도
[INFO] [pot_to_servo]: 전압 3.30V → 각도 180도
```

**확인** 가변저항을 한쪽 끝으로 돌리면 서보가 0도, 반대 끝이면 180도, 중앙이면 약 90도를 가리키면 정상입니다.

> 💡 `/pot`은 Day 2 `adc_sensor_hub.py`가 `Float64`(전압)로 발행합니다. 만약 ADC 허브를 0~255 원시값으로 발행하도록 바꿨다면 `V_MAX`를 `255.0`으로 바꾸세요(메시지 타입도 일치시킬 것).

---

## 심화 4 · 초음파 거리를 7세그먼트에 표시 (`/ultrasonic/range` → `/number`)

**핵심** Day 2 초음파가 발행하는 `/ultrasonic/range`(Range, m)를 구독해 **cm 정수**로 바꾼 뒤 `/number`(Int32)로 발행합니다. 본문 3-1의 `seg_display`가 이를 받아 7세그먼트에 표시합니다. 같은 값이 반복 발행되지 않도록 **값이 바뀔 때만** 내보냅니다.

`~/ros2_labs/sol4_range_seg.py` (노트북)

```python
#!/usr/bin/env python3
# 〔노트북〕 과제 심화4: /ultrasonic/range(m) → cm 정수 변환 → /number 발행
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range
from std_msgs.msg import Int32

class RangeToSeg(Node):
    def __init__(self):
        super().__init__('range_to_seg')
        self.pub = self.create_publisher(Int32, 'number', 10)
        self.sub = self.create_subscription(Range, 'ultrasonic/range', self.on_range, 10)
        self.last_cm = None
        self.get_logger().info('거리→7세그 변환 시작 — /ultrasonic/range 구독')

    def on_range(self, msg):
        cm = int(round(msg.range * 100.0))     # m → cm 정수
        if cm != self.last_cm:                 # 값이 바뀔 때만 발행
            out = Int32()
            out.data = cm
            self.pub.publish(out)
            self.last_cm = cm
            self.get_logger().info(f'거리 {msg.range:.3f}m → {cm}cm (표시 1의 자리: {cm % 10})')

def main(args=None):
    rclpy.init(args=args)
    node = RangeToSeg()
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

```bash
# 〔Pi〕 초음파 (Day 2) + 7세그먼트 노드 (본문 3-1)
$ python3 ~/ros2_labs/ultrasonic_range_pub.py
$ python3 ~/ros2_labs/seg_display.py
# 〔노트북〕 변환 노드
$ python3 ~/ros2_labs/sol4_range_seg.py
```

> ⚠️ **단일 7세그먼트는 한 자리(0~9)만** 표시합니다. 본문 `seg_display`가 `abs(msg.data) % 10`으로 1의 자리만 표시하므로, 거리가 12 cm면 `2`, 25 cm면 `5`가 나옵니다. 거리 변화를 한눈에 보려면 아래 둘 중 하나를 택하세요.
>
> - **데시미터(10 cm 단위) 표시**: `cm = int(round(msg.range * 10.0))` 으로 바꾸면 0~9가 0~90 cm를 한 자리로 나타냅니다(거리 0.37 m → `4`).
> - **두 자리 표시**: 7세그먼트 2개 또는 4자리 모듈(TM1637 등)을 멀티플렉싱해야 합니다(도전).

**확인** 손을 센서 앞에서 움직이면 7세그먼트 숫자가 거리에 따라 바뀌면 정상입니다.

---

## 도전 5 · 거리 비례 감속 폐루프 (`obstacle_guard` 개선)

**핵심** 본문 3-4의 `obstacle_guard`는 임계 거리에서 전진을 **딱 끊는(on/off)** 방식이었습니다. 이를 **가까울수록 느리게** 가는 비례 제어로 개선합니다. `STOP_DIST`(0.3 m) 이하면 정지, `STOP_DIST`~`SLOW_DIST`(0.8 m) 구간은 거리에 비례한 배율(0~1)로 감속, `SLOW_DIST` 이상이면 원래 속도로 통과시킵니다. 회전·후진은 그대로 허용합니다.

`~/ros2_labs/sol5_guard_prop.py` (노트북)

```python
#!/usr/bin/env python3
# 〔노트북〕 과제 도전5: 폐루프 비례 감속 — 가까울수록 전진 속도를 줄이고, 임계 이하면 정지
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range
from geometry_msgs.msg import Twist
from std_msgs.msg import String

STOP_DIST = 0.30    # m, 이 거리 이하: 전진 완전 정지
SLOW_DIST = 0.80    # m, 이 거리부터 감속 시작 (이상이면 원래 속도)

class ObstacleGuardProp(Node):
    def __init__(self):
        super().__init__('obstacle_guard_prop')
        self.distance = None
        self.create_subscription(Range, 'ultrasonic/range', self.on_range, 10)
        self.create_subscription(Twist, 'cmd_vel_in', self.on_cmd_in, 10)
        self.cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.status_pub = self.create_publisher(String, 'status', 10)
        self.get_logger().info(
            f'비례 감속 가드 시작 — {STOP_DIST}m 이하 정지, {STOP_DIST}~{SLOW_DIST}m 감속')

    def on_range(self, msg):
        self.distance = msg.range
        st = String()
        if self.distance is None:
            st.data = 'unknown'
        elif self.distance < STOP_DIST:
            st.data = 'danger'
        elif self.distance < SLOW_DIST:
            st.data = 'warn'
        else:
            st.data = 'ok'
        self.status_pub.publish(st)

    def speed_scale(self):
        # 거리 → 전진 속도 배율(0.0~1.0)
        if self.distance is None:
            return 1.0
        if self.distance < STOP_DIST:
            return 0.0
        if self.distance >= SLOW_DIST:
            return 1.0
        # STOP_DIST~SLOW_DIST 사이를 0~1로 선형 보간
        return (self.distance - STOP_DIST) / (SLOW_DIST - STOP_DIST)

    def on_cmd_in(self, msg):
        out = Twist()
        out.angular.z = msg.angular.z          # 회전은 항상 허용
        if msg.linear.x > 0.0:                 # 전진 명령만 감속 대상
            scale = self.speed_scale()
            out.linear.x = msg.linear.x * scale
            if scale < 1.0 and self.distance is not None:
                self.get_logger().warn(
                    f'장애물 {self.distance:.2f}m — 전진 속도 {scale*100:.0f}%로 감속')
        else:
            out.linear.x = msg.linear.x        # 후진·정지는 그대로 통과
        self.cmd_pub.publish(out)

def main(args=None):
    rclpy.init(args=args)
    node = ObstacleGuardProp()
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

```bash
# 〔Pi〕 초음파 · 모터 · 표시 허브
$ python3 ~/ros2_labs/ultrasonic_range_pub.py
$ python3 ~/ros2_labs/dc_motor_node.py
$ python3 ~/ros2_labs/display_hub.py
# 〔노트북〕 비례 감속 가드 (본문 obstacle_guard 대신 실행)
$ python3 ~/ros2_labs/sol5_guard_prop.py
# 〔노트북〕 조종은 /cmd_vel_in 으로 리매핑
$ ros2 run teleop_twist_keyboard teleop_twist_keyboard \
    --ros-args -r /cmd_vel:=/cmd_vel_in
```

```text
출력 ▶ (예시)  — 〔노트북〕 obstacle_guard_prop
[WARN] [obstacle_guard_prop]: 장애물 0.62m — 전진 속도 64%로 감속
[WARN] [obstacle_guard_prop]: 장애물 0.41m — 전진 속도 22%로 감속
[WARN] [obstacle_guard_prop]: 장애물 0.25m — 전진 속도 0%로 감속
```

**확인** 전진을 계속 누른 채 장애물에 다가가면, 멀 때는 빠르게, 가까워질수록 느려지다가 0.3 m 안에서 완전히 멈추면 정상입니다. 후진·회전은 거리와 무관하게 동작합니다.

> 💡 본문 가드와 같은 `/cmd_vel`·`/cmd_vel_in`·`/status` 인터페이스를 그대로 유지했으므로, 본문 `obstacle_guard` 대신 이 노드만 실행하면 됩니다. `SLOW_DIST`를 키우면 더 일찍·부드럽게 감속합니다.

---

## 도전 6 · LED 매트릭스(8×8) 화살표 표시 (`/cmd_vel` → 매트릭스)

**핵심** 74HC595 **2개**를 직렬(daisy-chain)로 연결해 8×8 매트릭스를 구동합니다. 한 칩은 **행 선택**, 다른 칩은 **열 데이터**를 담당하고, 16비트를 한 번에 밀어 넣은 뒤 래치합니다. 행을 빠르게 순회(멀티플렉싱)하려면 발행 처리(spin)와 별개로 **백그라운드 스레드**가 계속 화면을 새로고침해야 합니다. `/cmd_vel`을 구독해 전진이면 **↑**, 정지·후진이면 **↓** 화살표를 표시합니다.

`~/ros2_labs/sol6_matrix_arrow.py` (Pi)

```python
#!/usr/bin/env python3
# 〔Pi〕 과제 도전6: /cmd_vel(Twist) → 74HC595 2개(행 선택 + 열 데이터) → 8x8 매트릭스 화살표(↑/↓)
import time
import threading
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from gpiozero import OutputDevice

# 8행 비트맵(MSB=왼쪽 열). 전진=위 화살표, 정지/후진=아래 화살표
UP   = [0x18, 0x3C, 0x7E, 0xFF, 0x18, 0x18, 0x18, 0x18]
DOWN = [0x18, 0x18, 0x18, 0x18, 0xFF, 0x7E, 0x3C, 0x18]

class MatrixArrow(Node):
    def __init__(self):
        super().__init__('matrix_arrow')
        # 두 74HC595를 직렬(daisy-chain)로 연결, DS·SHCP·STCP 공유 (seg_display와 핀 충돌 주의)
        self.ds   = OutputDevice(16)   # 데이터
        self.shcp = OutputDevice(20)   # 시프트 클럭
        self.stcp = OutputDevice(21)   # 래치
        self.frame = list(UP)          # 현재 표시 비트맵(8행)
        self.lock = threading.Lock()
        self.running = True
        self.scan_thread = threading.Thread(target=self.scan_loop, daemon=True)
        self.scan_thread.start()
        self.create_subscription(Twist, 'cmd_vel', self.on_cmd, 10)
        self.get_logger().info('매트릭스 화살표 시작 — 전진 ↑ / 정지·후진 ↓')

    def shift16(self, row_select, col_data):
        # 16비트(행 선택 1바이트 + 열 데이터 1바이트)를 MSB first로 직렬 출력
        bits = (row_select << 8) | col_data
        for i in range(16):
            self.ds.value = (bits >> (15 - i)) & 0x01
            self.shcp.on(); self.shcp.off()
        self.stcp.on(); self.stcp.off()      # 래치(출력 반영)

    def scan_loop(self):
        # 행을 빠르게 순회(멀티플렉싱). 백그라운드 스레드에서 계속 새로고침
        while self.running:
            with self.lock:
                frame = list(self.frame)
            for r in range(8):
                self.shift16(1 << r, frame[r])
                time.sleep(0.001)            # 행당 1ms → 전체 약 125Hz

    def on_cmd(self, msg):
        pattern = UP if msg.linear.x > 0.05 else DOWN
        with self.lock:
            self.frame = list(pattern)

    def destroy_node(self):
        self.running = False
        time.sleep(0.05)                     # 스캔 스레드 종료 대기
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = MatrixArrow()
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

화살표 비트맵은 다음과 같습니다(`#`=점등).

```text
   UP(전진)        DOWN(정지)
  ...##...        ...##...
  ..####..        ...##...
  .######.        ...##...
  ########        ...##...
  ...##...        ########
  ...##...        .######.
  ...##...        ..####..
  ...##...        ...##...
```

```bash
# 〔Pi〕 매트릭스 노드
$ python3 ~/ros2_labs/sol6_matrix_arrow.py
# 〔노트북〕 전진/정지를 바꿔가며 화살표 전환 확인
$ ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.6}}"
$ ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0}}"
```

본문 3-2의 `dc_motor_node`도 `/cmd_vel`을 구독하므로, **모터와 매트릭스가 같은 명령에 동시에 반응**합니다. teleop로 조종하면 전진할 때 ↑, 멈추면 ↓가 뜹니다.

**확인** 전진 명령에 위 화살표, 정지·후진 명령에 아래 화살표가 깜빡임 없이 또렷하게 표시되면 정상입니다.

> ⚠️ 매트릭스 결선은 제품마다 **행/열 극성**이 다릅니다. 화살표가 뒤집히거나 음영이 반대로 나오면, ① `UP`/`DOWN` 비트를 반전(`b ^ 0xFF`)하거나 ② 행 선택을 반전(`~(1 << r) & 0xFF`)하거나 ③ 트랜지스터/저항으로 행 구동 전류를 확보해야 합니다.
>
> 💡 본문 `seg_display`와 이 노드를 **동시에** 쓰려면 두 74HC595 그룹의 `DS·SHCP·STCP` 핀이 서로 겹치지 않게 별도 핀으로 배선하세요. 화면이 어둡거나 잔상이 생기면 `scan_loop`의 행당 지연(`0.001`)을 줄여 새로고침 주파수를 높입니다.

---

## 실행 요약 (복붙용)

```bash
# ── 기본1: 상태 순환 (Pi: 표시 허브 / 노트북: 순환 발행) ──
python3 ~/ros2_labs/display_hub.py                 # Pi
python3 ~/ros2_labs/sol1_status_cycle.py           # 노트북

# ── 기본2: 서보 스윕 (Pi: 서보 / 노트북: 스윕) ──
python3 ~/ros2_labs/servo_node.py                  # Pi
python3 ~/ros2_labs/sol2_servo_sweep.py            # 노트북

# ── 심화3: 가변저항 → 서보 (Pi: ADC+서보 / 노트북: 매핑) ──
python3 ~/ros2_labs/adc_sensor_hub.py              # Pi (Day 2)
python3 ~/ros2_labs/servo_node.py                  # Pi
python3 ~/ros2_labs/sol3_pot_servo.py              # 노트북

# ── 심화4: 거리 → 7세그 (Pi: 초음파+7세그 / 노트북: 변환) ──
python3 ~/ros2_labs/ultrasonic_range_pub.py        # Pi (Day 2)
python3 ~/ros2_labs/seg_display.py                 # Pi
python3 ~/ros2_labs/sol4_range_seg.py              # 노트북

# ── 도전5: 비례 감속 폐루프 (Pi: 초음파+모터+표시 / 노트북: 가드+조종) ──
python3 ~/ros2_labs/ultrasonic_range_pub.py        # Pi
python3 ~/ros2_labs/dc_motor_node.py               # Pi
python3 ~/ros2_labs/display_hub.py                 # Pi
python3 ~/ros2_labs/sol5_guard_prop.py             # 노트북
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/cmd_vel_in

# ── 도전6: 매트릭스 화살표 (Pi: 매트릭스 / 노트북: 명령) ──
python3 ~/ros2_labs/sol6_matrix_arrow.py           # Pi
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.6}}"  # 노트북
```
