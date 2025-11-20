import struct
import time
import random
import glob
import os

import chipwhisperer as cw
import matplotlib.pyplot as plt
import numpy as np

TARGET_ARRAY_LENGTH = 15
correlation = 0.45

scope = cw.scope()
target = cw.target(scope, cw.targets.SimpleSerial)
scope.adc.samples = 200000

trace_cache = {}


def num_q():
    target.simpleserial_write('q', b"0")
    response = target.simpleserial_read('r', 4)
    return struct.unpack("<I", response)[0]


def reset_target():
    scope.io.nrst = 'low'
    time.sleep(0.05)
    scope.io.nrst = 'high_z'
    time.sleep(0.05)


# simpleserial_addcmd('x', 0, reset);
def reset():
    target.simpleserial_write('x', b"")
    response = target.simpleserial_read('r', 1)
    return response


# simpleserial_addcmd('p', 4, get_pt);
def get_pt(pt):
    scope.arm()
    target.simpleserial_write('p', bytes(pt))
    timeout = scope.capture()
    if timeout:
        raise RuntimeError("Capture timed out.")
    response = target.simpleserial_read('r', 1)
    trace = scope.get_last_trace()
    return trace


# simpleserial_addcmd('a', 30, check_arr);
def check_arr(arr):
    scope.arm()
    target.simpleserial_write('a', bytes(arr))
    timeout = scope.capture()
    if timeout:
        raise RuntimeError("Capture timed out.")
    response = target.simpleserial_read('r', 20)
    trace = scope.get_last_trace()
    return response.decode()


def get_trace_for_value(value):
    if value in trace_cache:
        return trace_cache[value]
    low, high = struct.pack('<H', value)
    pt = [0, low, high, 0]
    reset()
    trace = get_pt(pt)

    trace_cache[value] = trace
    return trace


def compute_transition_score(trace1, trace2):
    return np.max(np.abs(trace2 - trace1))


def binary_search(low=0, high=2**16-1):
    while (high - low) > 1:
        mid = (low + high) // 2
        
        trace_low = get_trace_for_value(low)
        trace_mid = get_trace_for_value(mid)
        trace_high = get_trace_for_value(high)
        
        # Transitions optimization
        diff_low_mid = compute_transition_score(trace_low, trace_mid)
        diff_mid_high = compute_transition_score(trace_mid, trace_high)
        if diff_low_mid < correlation and diff_mid_high < correlation:
            return None
        if diff_low_mid > diff_mid_high:
            high = mid
            final_diff = diff_low_mid
        else:
            low = mid
            final_diff = diff_mid_high
    if final_diff < correlation:
        return None
    else:
        return low


def test_key(arr):
    key = []
    arr = sorted(arr)
    for i in arr:
        low, high = struct.pack('<H', i)
        key.append(low)
        key.append(high)
    response = check_arr(key)
    return response


def main():
    reset_target()
    
    initial_queries = num_q()

    found = [2**16-1, 0]
    while len(found) < (TARGET_ARRAY_LENGTH + 2):
        for i in range(len(found)-1):
            low = found[i+1] + 1
            high = found[i]  - 1
            value = binary_search(low=low, high=high)
            if value:
                high = value - 1
                found.append(value)
            else:
                continue
        found.sort(reverse=True)
        print(f"Found so far: {found[1:-1]}")
    found = found[1:-1]
    flag = test_key(found)
    print(f"Flag: {flag}")
    final_queries = num_q()
    num_queries = final_queries - initial_queries
    print(f"Number of queries: {num_queries}")

if __name__ == "__main__":
    main()
