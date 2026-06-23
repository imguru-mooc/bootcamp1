# Day 2 · 과제 솔루션 (분산 통신 + 센서 입력)

> **대상** 강사용 솔루션 · Day 2 실습 자료의 과제 6문항(기본 2 · 심화 2 · 도전 2)
> **환경** 노트북(Ubuntu) + 라즈베리파이 4B · ROS 2 Humble
> **공통 전제** Day 2 센서 노드들(`button_pub`·`ultrasonic_range_pub`·`adc_sensor_hub`·`joystick_node`)이 Pi에서 동작하고, 양쪽 `ROS_DOMAIN_ID`가 같아야 합니다.

> ⚠️ 모든 코드는 **문법 검증(py_compile)** 만 거쳤습니다. 실물 센서·하드웨어가 없는 환경에서 작성했으므로 임계값·핀·부등호 방향은 **실제 환경에서 보정**이 필요합니다. 솔루션 파일은 `~/ros2_labs/`에 두는 것을 가정합니다.

---

## 기본 1 · `/temperature`를 rqt_plot으로 관찰

**핵심** 코드 없이 도구만 사용합니다. `Temperature` 메시지의 `temperature` 필드를 그래프로 띄우고, 서미스터를 손으로 잡아 온도가 오르는 곡선을 확인합니다.

```bash
# 〔Pi〕 ADC 허브 실행 (서미스터 발행 중)
$ python3 ~/ros2_labs/adc_sensor_hub.py

# 〔노트북〕 온도 그래프 (필드 경로까지 지정)
$ ros2 run rqt_plot rqt_plot /temperature/temperature
```

서미스터를 손가락으로 감싸면 1~2초 뒤 곡선이 상승하고, 놓으면 천천히 하강합니다. rqt_plot 우측 상단의 저장 아이콘으로 그래프를 캡처해 제출합니다.

**확인** 손으로 잡을 때 곡선이 우상향하면 정상입니다. 변화가 없으면 서미스터 분압 배선과 채널(CH2)을 점검하세요.

---

## 기본 2 · 가변저항 임계 발행 (`/pot_high`)

**핵심** `/pot`(전압, Float64)을 구독해 1.65 V(3.3 V의 절반) 이상이면 `/pot_high`(Bool)를 `true`로 발행합니다.

`~/ros2_labs/sol2_pot_high.py` (Pi)

```python
#!/usr/bin/env python3
# 〔Pi〕 과제2: /pot(전압)이 1.65V 이상이면 /pot_high(Bool)=true 발행
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64, Bool

THRESH = 1.65       # 가변저항 중앙(3.3V의 절반)

class PotHigh(Node):
    def __init__(self):
        super().__init__('pot_high')
        self.sub = self.create_subscription(Float64, 'pot', self.on_pot, 10)
        self.pub = self.create_publisher(Bool, 'pot_high', 10)
        self.get_logger().info('pot_high 시작 — /pot 구독 (임계 1.65V)')

    def on_pot(self, msg):
        high = msg.data >= THRESH
        self.pub.publish(Bool(data=high))

def main(args=None):
    rclpy.init(args=args)
    node = PotHigh()
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
# 〔Pi〕 ADC 허브 + 임계 노드
$ python3 ~/ros2_labs/adc_sensor_hub.py
$ python3 ~/ros2_labs/sol2_pot_high.py
# 〔노트북〕 가변저항을 돌리며 true/false 전환 확인
$ ros2 topic echo /pot_high
```

**확인** 가변저항을 중앙 이상으로 돌리면 `data: true`, 이하면 `data: false`.

---

## 심화 3 · 광센서 어두움 감지 (구독 노드)

**핵심** `/light`(상대 밝기 0~255)를 노트북에서 구독해 임계값 이하이면 "어두움"을 출력합니다. 매 프레임 출력하면 로그가 넘치므로 **상태가 바뀔 때만** 출력합니다.

`~/ros2_labs/sol3_light_monitor.py` (노트북)

```python
#!/usr/bin/env python3
# 〔노트북〕 과제3: /light가 임계값 이하(어두움)이면 출력 (전환 시에만)
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64

DARK = 60.0     # 0~255 상대값. 이 이하면 어두움 (배선에 따라 부등호 반대일 수 있음)

class LightMonitor(Node):
    def __init__(self):
        super().__init__('light_monitor')
        self.was_dark = False
        self.sub = self.create_subscription(Float64, 'light', self.on_light, 10)
        self.get_logger().info('밝기 모니터 시작 — /light 구독')

    def on_light(self, msg):
        dark = msg.data <= DARK
        if dark and not self.was_dark:
            self.get_logger().info(f'어두움 (light={msg.data:.0f})')
        elif not dark and self.was_dark:
            self.get_logger().info(f'밝아짐 (light={msg.data:.0f})')
        self.was_dark = dark

def main(args=None):
    rclpy.init(args=args)
    node = LightMonitor()
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
# 〔Pi〕 ADC 허브 / 〔노트북〕 모니터
$ python3 ~/ros2_labs/adc_sensor_hub.py            # Pi
$ python3 ~/ros2_labs/sol3_light_monitor.py        # 노트북
```

```text
출력 ▶ (예시)
[INFO] [light_monitor]: 어두움 (light=42)
[INFO] [light_monitor]: 밝아짐 (light=150)
```

**확인** 광센서를 손으로 가리면 "어두움", 떼면 "밝아짐"이 한 번씩 출력됩니다. 밝을 때 값이 작아지는 배선이면 부등호(`<=`)를 `>=`로 바꾸고 임계값을 조정합니다.

---

## 심화 4 · 장애물 근접 발행 (`/obstacle/near`)

**핵심** `/ultrasonic/range`(Range)를 구독해 0.3 m 이하이면 `/obstacle/near`(Bool)를 `true`로 발행합니다. Day 3 폐루프의 토대가 됩니다.

`~/ros2_labs/sol4_obstacle_near.py`

```python
#!/usr/bin/env python3
# 과제4: /ultrasonic/range가 0.3m 이하이면 /obstacle/near(Bool)=true 발행
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range
from std_msgs.msg import Bool

NEAR = 0.30

class ObstacleNear(Node):
    def __init__(self):
        super().__init__('obstacle_near')
        self.sub = self.create_subscription(Range, 'ultrasonic/range', self.on_range, 10)
        self.pub = self.create_publisher(Bool, 'obstacle/near', 10)
        self.get_logger().info('obstacle_near 시작 — 임계 0.3m')

    def on_range(self, msg):
        self.pub.publish(Bool(data=msg.range <= NEAR))

def main(args=None):
    rclpy.init(args=args)
    node = ObstacleNear()
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
# 〔Pi〕 초음파 / 어디서든 임계 노드
$ python3 ~/ros2_labs/ultrasonic_range_pub.py       # Pi
$ python3 ~/ros2_labs/sol4_obstacle_near.py
# 〔노트북〕 손을 센서 앞에 가까이
$ ros2 topic echo /obstacle/near
```

**확인** 손을 0.3 m 안으로 가져가면 `data: true`, 멀어지면 `false`. 이 노드는 노트북·Pi 어디서 실행해도 됩니다.

---

## 도전 5 · 센서 4종을 런치 하나로 (bringup)

두 가지 방법을 제시합니다. **(A)** 기존 스크립트를 그대로 묶는 간단한 방법, **(B)** 과제 의도대로 `pi_sensors` 패키지로 정식 패키징하는 방법.

### (A) 간단 — ExecuteProcess 런치

`~/ros2_labs/sol5_bringup_simple.launch.py`

```python
#!/usr/bin/env python3
# 과제5(간단): 표준 스크립트 4개를 한 번에 실행 (패키지화 없이)
import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess

def generate_launch_description():
    labs = os.path.join(os.path.expanduser('~'), 'ros2_labs')
    names = ['button_pub.py', 'ultrasonic_range_pub.py', 'adc_sensor_hub.py', 'joystick_node.py']
    return LaunchDescription([
        ExecuteProcess(cmd=['python3', os.path.join(labs, n)], output='screen') for n in names
    ])
```

```bash
# 〔Pi〕 네 센서 노드를 한 번에
$ ros2 launch ~/ros2_labs/sol5_bringup_simple.launch.py
```

### (B) 정식 — `pi_sensors` 패키지

패키지 구조:

```text
~/ros2_ws/src/pi_sensors/
├── package.xml
├── setup.py
├── resource/pi_sensors
├── pi_sensors/
│   ├── __init__.py
│   ├── button_pub.py            # 각 노드(기존 스크립트 복사, main 함수 포함)
│   ├── ultrasonic_range_pub.py
│   ├── adc_sensor_hub.py
│   └── joystick_node.py
└── launch/
    └── pi_sensors.launch.py
```

`setup.py` — **`import os` / `from glob import glob`을 `setuptools`보다 먼저** 두어야 `colcon build` 시 `NameError`가 나지 않습니다.

```python
import os
from glob import glob
from setuptools import setup

package_name = 'pi_sensors'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='robot',
    maintainer_email='robot@todo.todo',
    description='Day2 분산 센서 bringup',
    license='MIT',
    entry_points={
        'console_scripts': [
            'button_pub = pi_sensors.button_pub:main',
            'ultrasonic = pi_sensors.ultrasonic_range_pub:main',
            'adc_hub    = pi_sensors.adc_sensor_hub:main',
            'joystick   = pi_sensors.joystick_node:main',
        ],
    },
)
```

`launch/pi_sensors.launch.py`

```python
#!/usr/bin/env python3
# 과제5(패키지): pi_sensors 패키지의 4개 노드를 한 번에 실행
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(package='pi_sensors', executable='button_pub', name='button_publisher'),
        Node(package='pi_sensors', executable='ultrasonic', name='ultrasonic_publisher'),
        Node(package='pi_sensors', executable='adc_hub',    name='adc_sensor_hub'),
        Node(package='pi_sensors', executable='joystick',   name='joystick_node'),
    ])
```

```bash
# 〔Pi〕 빌드 후 실행
$ cd ~/ros2_ws && colcon build --packages-select pi_sensors
$ source install/setup.bash
$ ros2 launch pi_sensors pi_sensors.launch.py
```

**확인** 한 명령으로 네 센서 노드가 모두 뜨고, 노트북 `ros2 topic list`에 7개 토픽이 보이면 성공입니다.

> 💡 노드 코드를 패키지로 옮길 때는 각 파일에 `main()` 함수가 있어야 entry point가 동작합니다(Day 2 노드는 이미 충족). `package.xml`에는 `rclpy` 등 의존성을 `<exec_depend>`로 명시하세요.

---

## 도전 6 · 조이스틱으로 거북이 원격조종

**핵심** 조이스틱이 발행하는 `/joy_cmd`(Twist)를 turtlesim의 `/turtle1/cmd_vel`로 보냅니다. 가장 간단한 방법은 `topic_tools relay`, 속도 스케일을 조절하려면 작은 중계 노드를 씁니다.

### 방법 A — 그대로 중계 (topic_tools)

```bash
# 〔노트북〕 거북이
$ ros2 run turtlesim turtlesim_node
# 〔Pi〕 조이스틱
$ python3 ~/ros2_labs/joystick_node.py
# 〔노트북〕 토픽 중계
$ ros2 run topic_tools relay /joy_cmd /turtle1/cmd_vel
```

### 방법 B — 스케일 조정 중계 노드

조이스틱 `Twist`는 값이 작아 거북이가 느릴 수 있어, 배율을 곱해 보냅니다.

`~/ros2_labs/sol6_joy_to_turtle.py` (노트북)

```python
#!/usr/bin/env python3
# 〔노트북〕 과제6: 조이스틱(/joy_cmd) → turtlesim(/turtle1/cmd_vel) 중계(스케일)
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

LIN_SCALE = 2.0
ANG_SCALE = 2.0

class JoyToTurtle(Node):
    def __init__(self):
        super().__init__('joy_to_turtle')
        self.sub = self.create_subscription(Twist, 'joy_cmd', self.on_joy, 10)
        self.pub = self.create_publisher(Twist, 'turtle1/cmd_vel', 10)
        self.get_logger().info('조이스틱 → 거북이 중계 시작')

    def on_joy(self, msg):
        out = Twist()
        out.linear.x = msg.linear.x * LIN_SCALE
        out.angular.z = msg.angular.z * ANG_SCALE
        self.pub.publish(out)

def main(args=None):
    rclpy.init(args=args)
    node = JoyToTurtle()
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
# 〔노트북〕 거북이 + 중계
$ ros2 run turtlesim turtlesim_node
$ python3 ~/ros2_labs/sol6_joy_to_turtle.py
# 〔Pi〕 조이스틱
$ python3 ~/ros2_labs/joystick_node.py
```

**확인** 조이스틱을 앞뒤로 밀면 거북이가 전진/후진, 좌우로 기울이면 회전합니다. 너무 느리면 `LIN_SCALE`·`ANG_SCALE`을 키웁니다.

---

## 채점 가이드 (요약)

| 과제 | 핵심 확인 포인트 |
|---|---|
| 기본 1 | `/temperature/temperature` 그래프, 서미스터 가열 시 곡선 상승 |
| 기본 2 | `/pot ≥ 1.65V`에서 `/pot_high=true` 전환 |
| 심화 3 | `/light` 임계 이하에서 어두움 출력(전환 시에만) |
| 심화 4 | `/ultrasonic/range ≤ 0.3m`에서 `/obstacle/near=true` |
| 도전 5 | 런치 하나로 4개 노드 기동(패키지화 시 setup.py import 순서) |
| 도전 6 | `/joy_cmd → /turtle1/cmd_vel` 중계로 거북이 조종 |

> 💡 공통 점검: ① 양쪽 `ROS_DOMAIN_ID`·`ROS_LOCALHOST_ONLY=0` 일치, ② `rqt_plot`·`echo`는 필드 경로까지(`/pot/data`, `/temperature/temperature`), ③ 광센서 부등호 방향은 배선에 따라 다름. ④ 패키지화 시 `setup.py`의 `import os`/`glob`을 `setuptools`보다 먼저 둘 것.
