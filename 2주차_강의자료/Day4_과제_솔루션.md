# Day 4 · 과제 솔루션 (AI 통합 — 비전 인식)

> **대상** 강사용 솔루션 · Day 4 실습 자료의 과제 8문항(기본 2 · 심화 3 · 도전 3)
> **환경** 노트북(Ubuntu, 내장 카메라) + 라즈베리파이 4B · ROS 2 Humble
> **공통 전제** `webcam_pub.py`(노트북)가 실행되어 `/image_raw`가 발행 중이어야 합니다.

> ⚠️ 모든 코드는 **문법 검증(py_compile)** 만 거쳤습니다. 카메라·GPU·MediaPipe·실물 하드웨어가 없는 환경에서 작성했으므로, 임계값·핀·모델 입력 사양은 **실제 환경에서 보정**이 필요합니다. 솔루션 파일들은 `~/ros2_labs/`에 두는 것을 가정합니다.

---

## 기본 1 · 추적 색을 내 물체 색으로 바꾸기

**핵심** HSV 색공간에서 대상 색의 H(색상) 범위를 정합니다. 빨강은 H가 0과 180 양끝에 걸쳐 있어 **두 범위를 OR**로 합쳐야 합니다. 매번 코드를 고치지 않도록 **파라미터**로 뺍니다.

먼저 대상 색의 HSV 값을 눈으로 확인하는 것이 빠릅니다.

```bash
# 〔노트북〕 마우스로 픽셀의 HSV를 찍어보는 간단 도구
$ python3 - << 'PY'
import cv2
cap = cv2.VideoCapture(0)
def onclick(e, x, y, flags, hsv):
    if e == cv2.EVENT_LBUTTONDOWN:
        print('HSV =', hsv[y, x])
while True:
    ok, f = cap.read()
    hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
    cv2.imshow('pick', f); cv2.setMouseCallback('pick', onclick, hsv)
    if cv2.waitKey(1) == 27: break
PY
```

`~/ros2_labs/sol1_color_tracker.py`

```python
#!/usr/bin/env python3
# 과제1: HSV 범위를 파라미터로 받고, 빨강(0/180 양끝) 이중 범위 처리
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
from cv_bridge import CvBridge

class ColorTrackerParam(Node):
    def __init__(self):
        super().__init__('color_tracker')
        self.declare_parameter('h_lo', 0)
        self.declare_parameter('h_hi', 10)
        self.declare_parameter('s_lo', 120)
        self.declare_parameter('v_lo', 70)
        self.declare_parameter('red_wrap', True)     # 빨강 양끝 처리
        self.bridge = CvBridge()
        self.sub = self.create_subscription(Image, 'image_raw', self.on_image, 10)
        self.cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.img_pub = self.create_publisher(Image, 'tracked/image', 10)
        self.get_logger().info('색상 추적(파라미터) 시작')

    def build_mask(self, hsv):
        h_lo = self.get_parameter('h_lo').value
        h_hi = self.get_parameter('h_hi').value
        s_lo = self.get_parameter('s_lo').value
        v_lo = self.get_parameter('v_lo').value
        mask = cv2.inRange(hsv, np.array([h_lo, s_lo, v_lo]), np.array([h_hi, 255, 255]))
        if self.get_parameter('red_wrap').value and h_lo < 15:
            mask2 = cv2.inRange(hsv, np.array([180 - h_hi, s_lo, v_lo]), np.array([180, 255, 255]))
            mask = cv2.bitwise_or(mask, mask2)
        return mask

    def on_image(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        h, w = frame.shape[:2]
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        contours, _ = cv2.findContours(self.build_mask(hsv), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cmd = Twist()
        if contours:
            c = max(contours, key=cv2.contourArea)
            if cv2.contourArea(c) > 500:
                x, y, bw, bh = cv2.boundingRect(c)
                err = ((x + bw / 2.0) - w / 2.0) / (w / 2.0)
                cmd.angular.z = -1.5 * err
                cmd.linear.x = 0.2
                cv2.rectangle(frame, (x, y), (x + bw, y + bh), (0, 255, 0), 2)
        self.cmd_pub.publish(cmd)
        self.img_pub.publish(self.bridge.cv2_to_imgmsg(frame, 'bgr8'))

def main(args=None):
    rclpy.init(args=args)
    node = ColorTrackerParam()
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
# 〔노트북〕 파랑(예: H 100~130) 추적 — 코드 수정 없이 파라미터로
$ python3 ~/ros2_labs/sol1_color_tracker.py \
    --ros-args -p h_lo:=100 -p h_hi:=130 -p red_wrap:=false
```

**확인** `/tracked/image`에서 대상 색만 박스가 잡히고, 좌우로 옮기면 `/cmd_vel`의 `angular.z` 부호가 바뀝니다.

---

## 기본 2 · 다른 물체 추적하기 (`TARGET_CLASS`)

**핵심** YOLO(COCO 80클래스)의 클래스 이름을 바꾸면 됩니다. 상수 대신 **파라미터**로 빼면 실행 시 선택할 수 있습니다. 원본 `yolo_detector.py`에서 두 곳만 고칩니다.

```python
# (1) __init__ 안에서 상수 대신 파라미터 선언
self.declare_parameter('target_class', 'person')
self.target_class = self.get_parameter('target_class').value

# (2) on_image 안의 비교를 파라미터 값으로
if name == self.target_class and (best is None or conf > best[0]):
    best = (conf, (x1 + x2) / 2.0, (y1 + y2) / 2.0, x1, y1, x2, y2)
```

```bash
# 〔노트북〕 컵을 추적
$ python3 ~/ros2_labs/yolo_detector.py --ros-args -p target_class:=cup
```

```bash
# 사용 가능한 COCO 클래스 이름 확인
$ python3 -c "from ultralytics import YOLO; print(YOLO('yolov8n.pt').names)"
```

**확인** `cup`, `bottle`, `cell phone`, `chair` 등 화면의 다른 물체로 `/detection_label`·`/target`이 발행됩니다.

---

## 심화 3 · 가까울 때만 경보 (면적 기반)

**핵심** "가까움"은 바운딩박스가 **화면에서 차지하는 면적**으로 판단합니다. 먼저 `yolo_detector.py`가 대상 면적 비율을 `/target_area`(Float64)로 발행하게 살짝 고친 뒤, `ai_reaction`이 그 값으로 `danger`를 결정합니다.

검출기에 추가할 부분(요지):

```python
# yolo_detector.py — __init__
self.area_pub = self.create_publisher(Float64, 'target_area', 10)   # std_msgs/Float64 import 필요

# yolo_detector.py — on_image, best 가 있을 때
area = ((x2 - x1) * (y2 - y1)) / float(w * h)     # 0~1 정규화 면적
self.area_pub.publish(Float64(data=area))
```

`~/ros2_labs/sol3_ai_reaction.py`

```python
#!/usr/bin/env python3
# 과제3: 대상 바운딩박스 면적이 클 때(가까울 때)만 danger 경보
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from std_msgs.msg import Float64, String

AREA_DANGER = 0.15      # 화면 대비 면적 비율(0~1). 이 이상이면 '가까움'

class AiReactionArea(Node):
    def __init__(self):
        super().__init__('ai_reaction')
        self.pan = 90.0
        self.tilt = 90.0
        self.area = 0.0
        self.create_subscription(Point, 'target', self.on_target, 10)
        self.create_subscription(Float64, 'target_area', self.on_area, 10)
        self.pan_pub = self.create_publisher(Float64, 'servo_pan', 10)
        self.tilt_pub = self.create_publisher(Float64, 'servo_tilt', 10)
        self.status_pub = self.create_publisher(String, 'status', 10)
        self.last = self.get_clock().now()
        self.timer = self.create_timer(0.5, self.idle_check)
        self.get_logger().info('AI 반응(면적 기반) 시작')

    def on_area(self, msg):
        self.area = msg.data

    def on_target(self, msg):
        self.last = self.get_clock().now()
        self.pan  = max(0.0, min(180.0, self.pan  - 8.0 * msg.x))
        self.tilt = max(0.0, min(180.0, self.tilt + 8.0 * msg.y))
        self.pan_pub.publish(Float64(data=self.pan))
        self.tilt_pub.publish(Float64(data=self.tilt))
        if self.area >= AREA_DANGER and msg.z > 0.6:     # 가깝고 + 확실하면
            self.status_pub.publish(String(data='danger'))
        else:
            self.status_pub.publish(String(data='warn'))

    def idle_check(self):
        dt = (self.get_clock().now() - self.last).nanoseconds / 1e9
        if dt > 1.0:
            self.status_pub.publish(String(data='ok'))

def main(args=None):
    rclpy.init(args=args)
    node = AiReactionArea()
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

**확인** 대상이 멀면 `warn`(노랑), 카메라에 가까이 다가오면(박스 면적 ≥ 0.15) `danger`(빨강·부저). 임계값 `AREA_DANGER`로 민감도를 조절합니다.

---

## 심화 4 · 색 추적 + 폐루프 안전 (장애물 앞 정지)

**핵심** 색 추적의 `/cmd_vel`을 **`/cmd_vel_in`으로 리매핑**해 Day 3의 `obstacle_guard`를 거치게 합니다. 가드가 초음파를 보고 안전한 `/cmd_vel`만 모터로 보냅니다. 즉 **색을 따라가되 장애물 앞에서는 멈춥니다.**

노트북측 런치 — `~/ros2_labs/sol4_color_follow_safe.launch.py`

```python
#!/usr/bin/env python3
# 과제4: 색 추적 → 폐루프 안전 가드 (노트북측). Pi에서는 초음파·모터를 별도 실행.
import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess

def generate_launch_description():
    labs = os.path.join(os.path.expanduser('~'), 'ros2_labs')
    return LaunchDescription([
        # 색 추적: 출력 /cmd_vel 을 /cmd_vel_in 으로 리매핑 → 가드를 거치게
        ExecuteProcess(
            cmd=['python3', os.path.join(labs, 'color_tracker.py'),
                 '--ros-args', '-r', '/cmd_vel:=/cmd_vel_in'],
            output='screen'),
        # 폐루프 가드: /cmd_vel_in + /ultrasonic/range → /cmd_vel + /status
        ExecuteProcess(
            cmd=['python3', os.path.join(labs, 'obstacle_guard.py')],
            output='screen'),
    ])
```

```bash
# 〔노트북〕 카메라 + (색추적+가드) 런치
$ python3 ~/ros2_labs/webcam_pub.py
$ ros2 launch ~/ros2_labs/sol4_color_follow_safe.launch.py

# 〔Pi〕 초음파(거리) + DC 모터 + 표시
$ python3 ~/ros2_labs/ultrasonic_range_pub.py
$ python3 ~/ros2_labs/dc_motor_node.py
$ python3 ~/ros2_labs/display_hub.py
```

**데이터 흐름** `color_tracker(/cmd_vel→/cmd_vel_in) → obstacle_guard → /cmd_vel → dc_motor`. 가드는 거리 < 0.3 m면 전진을 차단하고 `/status`를 `danger`로 보냅니다.

**확인** 색 물체를 따라 회전·전진하다가, 앞에 장애물이 들어오면 전진이 멈추고 RGB가 빨강이 됩니다(회전은 계속 가능).

---

## 심화 5 · 손 제스처로 주행 지시

**핵심** 손가락의 펴짐 상태(엄지~소지 5개)를 조합해 제스처를 정의하고 `/cmd_vel`로 매핑합니다. 주먹=정지, 손바닥=전진, 검지만=좌회전, 검지+중지=우회전.

`~/ros2_labs/sol5_gesture_drive.py`

```python
#!/usr/bin/env python3
# 과제5: 손 제스처(주먹/손바닥/검지/검지+중지) → 주행 명령(/cmd_vel)
import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
from std_msgs.msg import String
from cv_bridge import CvBridge
import mediapipe as mp

TIPS = [4, 8, 12, 16, 20]
PIPS = [3, 6, 10, 14, 18]

class GestureDrive(Node):
    def __init__(self):
        super().__init__('gesture_drive')
        self.bridge = CvBridge()
        self.hands = mp.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=0.6)
        self.draw = mp.solutions.drawing_utils
        self.sub = self.create_subscription(Image, 'image_raw', self.on_image, 10)
        self.cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.name_pub = self.create_publisher(String, 'gesture_name', 10)
        self.img_pub = self.create_publisher(Image, 'gesture/image', 10)
        self.get_logger().info('제스처 주행 시작')

    def finger_states(self, lm, handed):
        st = [(lm[4].x < lm[3].x) if handed == 'Right' else (lm[4].x > lm[3].x)]
        for tip, pip in zip(TIPS[1:], PIPS[1:]):
            st.append(lm[tip].y < lm[pip].y)
        return st       # [엄지, 검지, 중지, 약지, 소지]

    def on_image(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = self.hands.process(rgb)
        cmd = Twist()
        name = 'none'
        if res.multi_hand_landmarks:
            hand = res.multi_hand_landmarks[0]
            handed = res.multi_handedness[0].classification[0].label
            f = self.finger_states(hand.landmark, handed)
            cnt = sum(1 for v in f if v)
            if cnt == 0:
                name = 'stop'                                # 주먹
            elif cnt == 5:
                name = 'forward'; cmd.linear.x = 0.4         # 손바닥
            elif f[1] and not f[2] and not f[3] and not f[4]:
                name = 'left'; cmd.angular.z = 0.8           # 검지만
            elif f[1] and f[2] and not f[3] and not f[4]:
                name = 'right'; cmd.angular.z = -0.8         # 검지+중지
            self.draw.draw_landmarks(frame, hand, mp.solutions.hands.HAND_CONNECTIONS)
        self.cmd_pub.publish(cmd)
        self.name_pub.publish(String(data=name))
        cv2.putText(frame, name, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        self.img_pub.publish(self.bridge.cv2_to_imgmsg(frame, 'bgr8'))

def main(args=None):
    rclpy.init(args=args)
    node = GestureDrive()
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
# 〔노트북〕
$ python3 ~/ros2_labs/sol5_gesture_drive.py
# 〔Pi〕 모터
$ python3 ~/ros2_labs/dc_motor_node.py
```

**확인** 주먹→정지, 손바닥→전진, 검지→좌회전, 검지+중지→우회전. `/gesture_name`으로 인식된 제스처를 확인합니다. 좌/우가 반대면 셀카 반전 때문이니 부호를 바꾸세요.

---

## 도전 6 · 런치로 비전 노드 선택 (YOLO ↔ 색상)

**핵심** `mode` 런치 인자와 `IfCondition`으로 둘 중 하나만 실행합니다.

`~/ros2_labs/sol6_vision_select.launch.py`

```python
#!/usr/bin/env python3
# 과제6: mode 인자로 YOLO 또는 색상 추적 중 하나를 선택 실행
import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch.conditions import IfCondition

def generate_launch_description():
    labs = os.path.join(os.path.expanduser('~'), 'ros2_labs')
    mode = LaunchConfiguration('mode')
    return LaunchDescription([
        DeclareLaunchArgument('mode', default_value='yolo', description='yolo 또는 color'),
        ExecuteProcess(
            cmd=['python3', os.path.join(labs, 'webcam_pub.py')], output='screen'),
        ExecuteProcess(
            cmd=['python3', os.path.join(labs, 'yolo_detector.py')], output='screen',
            condition=IfCondition(PythonExpression(["'", mode, "' == 'yolo'"]))),
        ExecuteProcess(
            cmd=['python3', os.path.join(labs, 'color_tracker.py')], output='screen',
            condition=IfCondition(PythonExpression(["'", mode, "' == 'color'"]))),
    ])
```

```bash
# 〔노트북〕 기본 YOLO
$ ros2 launch ~/ros2_labs/sol6_vision_select.launch.py
# 색상 추적으로
$ ros2 launch ~/ros2_labs/sol6_vision_select.launch.py mode:=color
```

**확인** `mode:=yolo`면 검출 노드만, `mode:=color`면 색추적 노드만 카메라와 함께 실행됩니다.

---

## 도전 7 · 노트북 YOLO vs Pi LiteRT 성능 비교

**핵심** 같은 장면에서 두 추론의 **FPS·지연·정확도**를 측정해 표로 정리합니다. FPS는 토픽 수신율로 측정합니다.

방법 ① 빠른 측정 — `ros2 topic hz`:

```bash
# 〔노트북〕 YOLO 검출 출력 빈도
$ ros2 topic hz /detection/image
# 〔Pi〕 LiteRT 분류 출력 빈도
$ ros2 topic hz /pi_class
```

방법 ② 코드로 측정 — `~/ros2_labs/sol7_fps_probe.py` (지정 토픽의 수신 FPS):

```python
#!/usr/bin/env python3
# 과제7: 지정 토픽의 수신 FPS 측정 (YOLO vs LiteRT 비교용)
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class FpsProbe(Node):
    def __init__(self):
        super().__init__('fps_probe')
        self.declare_parameter('topic', 'detection_label')
        topic = self.get_parameter('topic').value
        self.sub = self.create_subscription(String, topic, self.on_msg, 10)
        self.t0 = time.time(); self.n = 0
        self.get_logger().info(f'{topic} 수신 FPS 측정 시작')

    def on_msg(self, msg):
        self.n += 1
        dt = time.time() - self.t0
        if dt >= 2.0:
            self.get_logger().info(f'{self.n / dt:.1f} FPS')
            self.t0 = time.time(); self.n = 0

def main(args=None):
    rclpy.init(args=args)
    node = FpsProbe()
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
$ python3 ~/ros2_labs/sol7_fps_probe.py --ros-args -p topic:=detection_label   # 노트북 YOLO
$ python3 ~/ros2_labs/sol7_fps_probe.py --ros-args -p topic:=pi_class          # Pi LiteRT
```

**보고서 표 양식(예시값 — 실제 측정으로 채움)**

| 항목 | 노트북 YOLO(yolov8n) | Pi LiteRT(MobileNet) |
|---|---|---|
| 평균 FPS | 측정 | 측정 |
| 1프레임 지연 | 측정(ms) | 측정(ms) |
| 정확도(체감) | 높음 | 보통 |
| 네트워크 의존 | 영상 전송 필요 | 로컬 |
| 결론 | 정밀 검출에 적합 | 저지연 반응에 적합 |

**확인** 두 추론의 FPS 숫자와 트레이드오프를 표로 비교해 제출합니다.

---

## 도전 8 · 감정 분류로 확장 (FER)

**핵심** 입 모양 휴리스틱(4-6-2) 대신 **감정 분류 모델(FER)** 로 명명된 감정(happy·sad·angry·surprise 등)을 얻어 하드웨어에 매핑합니다.

```bash
# 〔노트북〕 FER 설치 (TensorFlow 의존, 용량 큼)
$ pip3 install fer
```

`~/ros2_labs/sol8_emotion_control.py`

```python
#!/usr/bin/env python3
# 과제8: FER 감정 분류 → 감정별 하드웨어 반응(/status, /lcd_text)
import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
from fer import FER

# 감정 → 상태(표시 허브 ok/warn/danger/off)
EMO_STATUS = {'happy': 'ok', 'surprise': 'warn', 'angry': 'danger', 'fear': 'danger',
              'sad': 'warn', 'disgust': 'warn', 'neutral': 'off'}

class EmotionControl(Node):
    def __init__(self):
        super().__init__('emotion_control')
        self.bridge = CvBridge()
        self.detector = FER(mtcnn=False)
        self.sub = self.create_subscription(Image, 'image_raw', self.on_image, 10)
        self.status_pub = self.create_publisher(String, 'status', 10)
        self.lcd_pub = self.create_publisher(String, 'lcd_text', 10)
        self.img_pub = self.create_publisher(Image, 'emotion/image', 10)
        self.get_logger().info('감정 제어 시작 — /image_raw 구독')

    def on_image(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        emo = 'neutral'
        res = self.detector.detect_emotions(frame)
        if res:
            scores = res[0]['emotions']
            emo = max(scores, key=scores.get)
            x, y, bw, bh = res[0]['box']
            cv2.rectangle(frame, (x, y), (x + bw, y + bh), (0, 255, 0), 2)
        self.status_pub.publish(String(data=EMO_STATUS.get(emo, 'off')))
        self.lcd_pub.publish(String(data=f'emo: {emo}'))
        cv2.putText(frame, emo, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        self.img_pub.publish(self.bridge.cv2_to_imgmsg(frame, 'bgr8'))

def main(args=None):
    rclpy.init(args=args)
    node = EmotionControl()
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
# 〔노트북〕
$ python3 ~/ros2_labs/sol8_emotion_control.py
# 〔Pi〕 표시장치
$ python3 ~/ros2_labs/display_hub.py
$ python3 ~/ros2_labs/lcd_display.py
```

**감정 → 하드웨어 매핑(예)**

| 감정 | 상태(`/status`) | 표현 |
|---|---|---|
| happy | ok | 초록 |
| surprise / sad / disgust | warn | 노랑·부저 |
| angry / fear | danger | 빨강·부저 |
| neutral | off | 꺼짐 |

**확인** 표정을 지으면 LCD에 감정 이름이, RGB·부저에 해당 반응이 나타납니다. FER는 무거우므로 프레임레이트가 낮습니다(필요 시 몇 프레임에 한 번만 추론).

---

## 채점 가이드 (요약)

| 과제 | 핵심 확인 포인트 |
|---|---|
| 기본 1 | HSV 범위 파라미터화 + 빨강 이중범위, `/tracked/image`에 대상만 검출 |
| 기본 2 | `target_class` 변경으로 다른 COCO 객체 추적 |
| 심화 3 | `/target_area` 추가 + 면적 임계값으로 `danger` 분기 |
| 심화 4 | `/cmd_vel`→`/cmd_vel_in` 리매핑으로 가드 경유, 장애물 앞 정지 |
| 심화 5 | 손가락 상태 조합으로 4개 제스처 → `/cmd_vel` 매핑 |
| 도전 6 | `mode` 인자 + `IfCondition`으로 노드 선택 실행 |
| 도전 7 | FPS 측정값과 트레이드오프 표 제출 |
| 도전 8 | FER 감정 라벨 → 하드웨어 반응 매핑 동작 |

> 💡 공통 감점/주의: ① 카메라 좌우 반전 미보정, ② 모터 외부전원·GND 공통 누락, ③ 머신 간 `ROS_DOMAIN_ID` 불일치로 토픽 미수신. 실행 전 이 세 가지를 먼저 점검하도록 안내하세요.
