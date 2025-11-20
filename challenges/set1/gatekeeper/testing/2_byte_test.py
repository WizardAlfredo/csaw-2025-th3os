import chipwhisperer as cw
import matplotlib.pyplot as plt
from string import printable, ascii_lowercase, ascii_uppercase, digits
from itertools import product
import time


charset = ascii_lowercase + digits + ascii_uppercase
charset_test =  [f"X{c}" for c in charset] + [f"Y{c}" for c in charset]  + [f"Z{c}" for c in charset] 

scope = cw.scope()
target = cw.target(scope, cw.targets.SimpleSerial)

scope.adc.clk_src = "ext"
scope.adc.clk_freq = 60e6


def reset_target():
    scope.io.nrst = 'low'
    time.sleep(0.05)
    scope.io.nrst = 'high_z'
    time.sleep(0.05)


def guess(password):
    start = time.perf_counter()
    target.simpleserial_write('b', password)
    response = target.simpleserial_read('r', 1)
    end = time.perf_counter()
    if response == b"\x00":
        response = 0
    elif response == b"\x01":
        response = 1
    else:
        response = 2
    timing = end - start
    # print(f"{end} - {start} = {timing}")
    return response, timing


def main():
    reset_target()
    scope.default_setup()

    inside = b"7rU3ncr"

    for _ in range(10):
        timing = 0

        prefix = b"gk2{"
        suffix = b"}"
        padding = (10 - len(inside)) * b"#"

        counter = 0
        for tmp_letters in charset_test:
            tmp_letters = "".join(tmp_letters)
            password = prefix + inside + tmp_letters.encode() + padding + suffix
            response, tmp_timing = guess(password)
            print(f"{password} {response} {tmp_timing}")

            if tmp_timing > timing:
                timing = tmp_timing
                letters = tmp_letters

            counter += 1
            if (counter % 100) == 0:
                print(counter)

            if response == 1:
                response, _ = guess(password)
                print(f"Got: {response} for Password: {password.decode()}")
                scope.dis()
                target.dis()
                exit()


if __name__ == "__main__":
    main()