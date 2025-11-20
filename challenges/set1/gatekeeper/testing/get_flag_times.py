import chipwhisperer as cw
from string import ascii_lowercase, digits, ascii_uppercase
import time
from collections import Counter


scope = cw.scope()
target = cw.target(scope, cw.targets.SimpleSerial)
scope.default_setup()


def measure_response_time(password, n=10):
    times = []
    #print(f"== PASSWORD {password} ==")
    for _ in range(n):
        # Send and time response
        start = time.perf_counter()
        target.simpleserial_write('b', password)
        resp = target.simpleserial_read('r', 1)
        end = time.perf_counter()
        if resp is not None:
            elapsed = (end - start) * 1000000
            #print(f"DEBUG elapsed = {elapsed}")
            times.append(elapsed)
    
    import numpy as np
    return np.mean(times)

def find_char_response_timing(known_prefix, charset):

    test_pw = known_prefix + b'!' * (16 - len(known_prefix)) + b'}'
    sample_time = measure_response_time(test_pw)
    print(f"+ Flag time: {test_pw}:{sample_time}")

    return

# ========================================
#              GATEKEEPER 2              #
# ========================================

print("\n" + "="*70)
print("GATEKEEPER 2")
print("="*70)

gk2_password = b'gk2{7rU3ncrYkIND}'
charset = ascii_lowercase + ascii_uppercase + digits

print(f"\nKnown: {gk2_password.decode()}")

for pos in range(13):
    next_char = find_char_response_timing(gk2_password[:4+pos], charset)



print(f"\n" + "="*70)
print(f"FINAL: {gk2_password.decode()}")
print("="*70)


scope.dis()
target.dis()
