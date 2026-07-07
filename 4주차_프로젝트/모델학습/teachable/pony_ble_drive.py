# pony_ble_drive.py  ----  웹앱(음성/제스처/Teachable Machine) 명령 수신 -> 포니봇 주행
#   받는 명령: forward / backward / left / right / stop
#   ※ 웹앱 필터가 namePrefix 'ESP' 이므로 기기명은 ESP- 로 시작하면 됩니다.
from time import sleep
import ble_library
import bluetooth
from ai_ponybot import i2c, PonyMotor

motor = PonyMotor(i2c)

ble = bluetooth.BLE()
p = ble_library.BLESimplePeripheral(ble, 'ESP-000')

SPEED     = 60         # 주행 속도
INVERT_FB = False      # 앞뒤가 반대로 가면 True

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
        print('알 수 없는 명령:', cmd); return
    print('CMD:', cmd)

p.on_write(on_rx)
print("포니봇 BLE 대기 중... (기기명 ESP-000)")

while True:
    if not p.is_connected():
        motor.drive('stop')        # 연결 끊기면 안전 정지
    sleep(0.1)
