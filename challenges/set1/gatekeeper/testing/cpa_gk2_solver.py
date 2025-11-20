import chipwhisperer as cw
import matplotlib.pyplot as plt
from string import ascii_lowercase, ascii_uppercase, digits
import time


scope = cw.scope()
target = cw.target(scope, cw.targets.SimpleSerial)


def reset_target(scope):
    scope.io.nrst = 'low'
    time.sleep(0.05)
    scope.io.nrst = 'high_z'
    time.sleep(0.05)


def guess(password):
    # reset_target(scope)
    scope.arm()
    target.simpleserial_write('b', password)
    timeout = scope.capture()
    if timeout:
        raise RuntimeError("Capture timed out. Check trigger wiring/state and edge selection.")

    response = target.simpleserial_read('r', 1)
    response = 0 if response == b"\x00" else 1

    trace = scope.get_last_trace()
    return response, trace


def main():
    scope.default_setup()

    for l in ascii_lowercase + ascii_uppercase + digits:
        password = b"gk2{" + l.encode() + 11 * b"0" + b"}"
        response, trace = guess(password)
        print(f"{l} {response} {sum(trace[:500])}")
        plt.figure(figsize=(12, 3))
        plt.plot(trace[:500])
        plt.title(f"Trace for tested character: '{l}'")
        plt.xlabel("Time Samples")
        plt.ylabel("Power Consumption (Voltage)")
        plt.grid(True)
        plt.savefig(f"traces/{str(ord(l))}.png", dpi=300)
        plt.close()

    target.simpleserial_write('q', b"0")
    response = target.simpleserial_read('r', 4)
    if response is not None:
        print(f"Number of Queries (cumulative): {int.from_bytes(response, byteorder='little', signed=False)}") #number of queries since powerup


if __name__ == "__main__":
    main()
