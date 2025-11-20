import chipwhisperer as cw
from string import ascii_lowercase, digits, ascii_uppercase
import time
from collections import Counter


scope = cw.scope()
target = cw.target(scope, cw.targets.SimpleSerial)
scope.default_setup()


def measure_response_time(password, n=5):
    start = time.perf_counter()
    target.simpleserial_write('b', password)
    resp = target.simpleserial_read('r', 1)
    end = time.perf_counter()
    if resp is not None:
        elapsed = (end - start)    
    return elapsed


def get_sample_time(known_prefix):
    test_pw = known_prefix + b'#' * (16 - len(known_prefix)) + b'}'
    sample_time = measure_response_time(test_pw)
    return sample_time


def find_last_chars(known_prefix, charset, sample_time):
    delta_max = 0
    for c in charset:
        test_pw = known_prefix + c.encode() + b'#' * (17 - len(known_prefix) - 2) + b'}'
        test_time = measure_response_time(test_pw)
        delta = abs(sample_time - test_time)
        if delta > 0.002:
            winner = c
            break
    return winner, test_time



def main():
    # Get the last characters of the flag
    charset = ascii_lowercase + ascii_uppercase + digits
    gk2_password = b'gk2{7rU3'
    
    sample_time = get_sample_time(gk2_password)

    for pos in range(16-len(gk2_password)):
        next_char, next_time = find_last_chars(gk2_password, charset, sample_time)
        gk2_password += next_char.encode()
        print(f"{gk2_password.decode()}", end='\r', flush=True)
        sample_time = next_time


    gk2_password += b'}'
    print(f"{gk2_password.decode()}", end='\r', flush=True)
    
    
    
    # Verify the flag
    target.simpleserial_write('b', gk2_password)
    resp = target.simpleserial_read('r', 1, timeout=500)

    if resp and resp[0] == 1:
        print(f"\nVerified flag: {gk2_password.decode()}")
    else:
        print(f"\nVerification fail, response: {resp}")


    scope.dis()
    target.dis()


if __name__ == "__main__":
    main()
