import time
from string import printable

import chipwhisperer as cw
import matplotlib.pyplot as plt
import numpy as np


CHARSET = printable[:-6]
PASSWORD_LENGTH = 12

scope = cw.scope()
target = cw.target(scope, cw.targets.SimpleSerial)
scope.default_setup()


def reset_target(): 
    scope.io.nrst = 'low'
    time.sleep(0.05)
    scope.io.nrst = 'high_z'
    time.sleep(0.05)


def authenticate(key):
    scope.arm()
    target.simpleserial_write('a', key)

    timeout = scope.capture()
    if timeout:
        raise RuntimeError("Capture timed out.")

    response = target.simpleserial_read('r', 18)
    trace = scope.get_last_trace()
    return response, trace


def main():
    queries = 0

    # Sample timing 
    reference_password = PASSWORD_LENGTH * b" "
    _, trace_sample = authenticate(reference_password)
    queries += 1

    password = b""

    # Find password
    for i in range(PASSWORD_LENGTH):
        padding = (PASSWORD_LENGTH - 1 - len(password)) * b" "
        for character in CHARSET:
            character = character.encode()
            key = password + character + padding
            response, trace = authenticate(key)
            queries += 1
            correlation = np.corrcoef(trace, trace_sample)[0, 1]

            print(f'Testing: {key.decode()}, Correlation: {correlation:.3f}')

            if correlation < 0.7:
                password += character
                trace_sample = trace
                break
  
    print(f"\nGot response {response} for password: {password.decode()}")
    print(f"Number of queries: {queries}")


if __name__ == "__main__":
    main()
