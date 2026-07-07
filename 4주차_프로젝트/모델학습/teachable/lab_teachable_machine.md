# 실습 — 내가 학습시킨 AI로 포니봇 제어 (Teachable Machine 이미지) 🧠🤖

> **멀티모달 인지 기반 피지컬 AI 로봇 시스템 구현 과정**
> 학생이 **직접 사진을 모아 AI 모델을 학습**시키고, 그 모델을 브라우저에 불러와
> 사물을 보여주면 포니봇이 움직입니다. **데이터 수집 → 학습 → 배포 → 로봇 제어** 의 AI 전 과정을 체험합니다.

---

## 0. 전체 그림

```
[Teachable Machine]        [내 웹앱 (HTTPS)]                 [포니봇]
 사진으로 모델 학습   →    모델 로딩(TF.js) → 카메라 분류    ble_library.py
 Export(Upload) → URL      → 클래스 → 명령 매핑 → Web BT ──▶ on_rx ─▶ 주행
```

- 분류는 **폰 안에서** 돌아갑니다(서버 불필요).
- 보내는 명령은 기존과 동일: `forward` `backward` `left` `right` `stop` → **같은 수신 펌웨어** 사용.

---

## 1. 사전 준비

| 파일 | 역할 |
|------|------|
| `ble_library.py` | BLE(Nordic UART) 라이브러리 — 보드 루트(`/`)에 업로드 |
| `ai_ponybot` 패키지 | `PonyMotor`(주행) |
| `pony_ble_drive.py` | 명령 수신 펌웨어(부록) |
| `teachable.html` | AI 제어 웹앱 |

> 보드에서 `pony_ble_drive.py` 실행 → 셸에 `포니봇 BLE 대기 중... (기기명 ESP-000)` 이 떠야 준비 완료.

---

## 2. STEP 1 — Teachable Machine에서 모델 학습

1. 브라우저에서 **teachablemachine.withgoogle.com** 접속 → **Get Started** → **Image Project** → **Standard image model**
2. **클래스(Class)** 를 만듭니다. 명령마다 하나씩 + 정지용 배경 클래스 권장. 예:
   - `사과` (→ 전진), `컵` (→ 후진), `책` (→ 좌회전), `펜` (→ 우회전), `배경` (→ 정지)
3. 각 클래스에서 **Webcam → Hold to Record** 로 그 사물 사진을 **여러 각도·거리로 50~100장** 찍습니다.
   - `배경` 클래스는 **아무것도 없는 화면**을 찍어 둡니다(아무것도 안 보이면 정지).
4. **Train Model** 클릭 → 학습 완료까지 대기.
5. 우측 **Preview** 에서 사물을 비춰 분류가 잘 되는지 확인.

> 💡 잘 맞추는 비결: **다양한 배경·조명·각도**로 촬영, 클래스마다 **사진 수를 비슷하게**, 실제 사용할 환경과 비슷하게.

---

## 3. STEP 2 — 모델 내보내기 (URL 받기)

1. Preview 위의 **Export Model** 클릭
2. 상단 탭에서 **TensorFlow.js** 선택
3. **Upload (shareable link)** → **Upload my model** 클릭
4. 잠시 후 나오는 주소를 복사합니다 (이게 우리가 쓸 모델 URL):
   ```
   https://teachablemachine.withgoogle.com/models/XXXXXXXX/
   ```

> 이 방식은 모델 파일을 따로 관리할 필요가 없어 가장 간단합니다. (구글이 HTTPS로 호스팅)

---

## 4. STEP 3 — 웹앱에 모델 연결

1. `teachable.html`을 **HTTPS 주소**로 엽니다 (배포는 6장 참고).
2. **① 모델 URL** 칸에 위에서 복사한 주소를 붙여넣고 **모델 불러오기**.
3. 성공하면 상태줄에 `✅ 모델 로딩 완료! 클래스: 사과, 컵, ...` 이 뜨고, 아래 **② 매핑** 영역이 나타납니다.

---

## 5. STEP 4 — 클래스 → 명령 매핑 & 제어

1. **② 클래스 → 명령 연결** 에서 각 사물에 동작을 고릅니다.
   - 클래스 이름에 전진/후진/좌/우 같은 단어가 있으면 **자동으로 추정**되어 있습니다. 필요하면 드롭다운으로 바꾸세요.
   - `배경/없음` 클래스는 **정지**로 두면 안전합니다.
2. **③ 포니봇 연결** → 목록에서 **ESP-000** 선택
3. **④ 카메라 시작** → 카메라 허용
4. 학습한 사물을 카메라에 보여주면, **예측 막대**에서 확률이 오르고 → 임계값(기본 80%)을 넘고 잠깐 유지되면 → 해당 명령이 전송되어 차가 움직입니다.
5. **신뢰도 임계값** 슬라이더로 민감도 조절(자주 오작동하면 ↑, 잘 안 나가면 ↓).

> 같은 결과가 4프레임 유지될 때만 보내 떨림을 막습니다. 손/사물을 치우면 `배경`이 잡혀 정지합니다.

---

## 6. GitHub로 웹앱 배포 (HTTPS)

카메라·블루투스는 **HTTPS에서만** 동작합니다. (`file://`·`content://`·`blob` 주소는 안 됨)

1. 공개 저장소에 **`teachable.html`** 업로드
2. **Settings → Pages → Branch `main` / `/(root)` → Save**
3. 1~2분 뒤 `Your site is live at ...` 주소 확인 → 폰 Chrome에서:
   ```
   https://<아이디>.github.io/<저장소>/teachable.html
   ```
   또는 설정 없이 즉시:
   ```
   https://cdn.jsdelivr.net/gh/<아이디>/<저장소>@main/teachable.html
   ```
> 모델은 Teachable Machine URL에서 불러오므로 **저장소에는 HTML만** 있으면 됩니다.

폰에서 열 때: **블루투스 ON · 위치 ON**, **Chrome**(인앱 브라우저 ❌), 카메라 권한 허용, 안드로이드 사용(iPhone Safari 미지원).

---

## 7. 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| 모델 로딩 실패 | URL 오타/끝 슬래시 | 주소 끝에 `/` 포함, `https://teachablemachine.../models/…/` 형태 |
| 〃 | HTTP로 열림 | 웹앱을 **HTTPS**로 열기 |
| 카메라 안 켜짐 | 권한·HTTPS | 카메라 허용, https 주소 확인 |
| 분류가 자꾸 틀림 | 학습 데이터 부족/편향 | 각도·배경·조명 다양화, 사진 추가, 임계값 ↑ |
| 계속 같은 명령 | `배경` 클래스 없음 | 빈 화면 클래스 추가→정지로 매핑 |
| 장치 안 보임 | 위치 OFF/다른 탭 연결 | 위치 ON, 다른 BLE 연결 해제, 보드 Ctrl+D |
| 앞뒤 반대 | 모터 방향 | 펌웨어 `INVERT_FB = True` |

---

## 8. 도전과제 🎯

> **8-A. 속도 제스처 추가** — `빠르게`/`천천히` 클래스를 만들어 속도(예: 90/40)도 바꿔 보세요. (명령에 `forward,90` 형식 추가 + 펌웨어 파싱)

> **8-B. 8방향으로 확장** — 대각선용 클래스를 추가해 `mecanum` 8방향 명령까지 매핑해 보세요.

> **8-C. 내 손모양 모델** — 사물 대신 **손모양(가위/바위/보)** 으로 학습시켜 제어해 보세요. (제스처 인식을 직접 학습으로 구현)

> **8-D. 오작동 줄이기** — 임계값·STABLE 프레임 수를 바꿔가며 정확도와 반응속도의 균형을 찾아 보세요.

---

## 부록 — `pony_ble_drive.py` (수신 펌웨어)

> `ble_library.py`와 함께 보드에 올리고 실행하세요. (음성·제스처 실습과 동일 파일)

```python
# pony_ble_drive.py
from time import sleep
import ble_library
import bluetooth
from ai_ponybot import i2c, PonyMotor

motor = PonyMotor(i2c)

ble = bluetooth.BLE()
p = ble_library.BLESimplePeripheral(ble, 'ESP-000')

SPEED     = 60
INVERT_FB = False      # 앞뒤가 반대면 True

def on_rx(v):
    cmd = v.strip().lower()
    if not cmd: return
    if INVERT_FB:
        if   cmd == 'forward':  cmd = 'backward'
        elif cmd == 'backward': cmd = 'forward'
    if   cmd == 'forward':  motor.drive('forward',  SPEED)
    elif cmd == 'backward': motor.drive('backward', SPEED)
    elif cmd == 'left':     motor.drive('left',     SPEED)
    elif cmd == 'right':    motor.drive('right',    SPEED)
    elif cmd == 'stop':     motor.drive('stop')
    else:
        print('알 수 없는 명령:', cmd); return
    print('CMD:', cmd)

p.on_write(on_rx)
print("포니봇 BLE 대기 중... (기기명 ESP-000)")

while True:
    if not p.is_connected():
        motor.drive('stop')
    sleep(0.1)
```

> 이 실습으로 학생은 **자신이 만든 AI**가 로봇을 움직이는 전 과정을 경험합니다 —
> 데이터를 모으고, 학습시키고, 브라우저에 올려, 무선으로 로봇을 제어합니다.
