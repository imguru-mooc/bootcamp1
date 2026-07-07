# pony_ble_drive.py ---- AI 웹앱(전이학습/음성/제스처/TM) 명령 수신 -> 포니봇 주행
#   받는 명령: forward / backward / left / right / stop
#   ※ 웹앱 필터가 namePrefix 'ESP' 이므로 기기명은 ESP- 로 시작하면 됩니다.
#   ※ ble_library.py, ai_ponybot.py(+microbit.py 심)가 보드에 있어야 합니다.
from time import sleep
import ble_library
import bluetooth
from ai_ponybot import i2c, PonyMotor, PonyOLED

motor = PonyMotor(i2c)
oled  = PonyOLED(i2c)

ble = bluetooth.BLE()
p = ble_library.BLESimplePeripheral(ble, 'ESP-000')

SPEED     = 60         # 주행 속도 (0~100)
INVERT_FB = False      # 앞뒤가 반대로 가면 True 로 바꾸세요

def show(line0, line1=""):
    oled.clear()
    oled.write_line(0, line0)
    if line1:
        oled.write_line(1, line1)
    oled.show()

def on_rx(v):
    cmd = v.strip().lower()
    if not cmd:
        return
    if INVERT_FB:
        if   cmd == 'forward':  cmd = 'backward'
        elif cmd == 'backward': cmd = 'forward'

    if   cmd == 'forward':  motor.drive('forward',  SPEED)
    elif cmd == 'backward': motor.drive('backward', SPEED)
    elif cmd == 'left':     motor.drive('left',     SPEED)   # 좌회전
    elif cmd == 'right':    motor.drive('right',    SPEED)   # 우회전
    elif cmd == 'stop':     motor.drive('stop')
    else:
        print('알 수 없는 명령:', cmd)
        return
    print('CMD:', cmd)
    show('AI DRIVE', 'CMD: ' + cmd)

p.on_write(on_rx)
show('BLE WAITING', 'name: ESP-000')
print("포니봇 BLE 대기 중... (기기명 ESP-000)")

was_connected = False
while True:
    c = p.is_connected()
    if c and not was_connected:
        show('CONNECTED', 'show your card!')
    if not c:
        motor.drive('stop')        # 연결 끊기면 안전 정지
        if was_connected:
            show('BLE WAITING', 'name: ESP-000')
    was_connected = c
    sleep(0.1)
