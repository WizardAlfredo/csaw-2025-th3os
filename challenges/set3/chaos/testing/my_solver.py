import struct
import time
import random

import chipwhisperer as cw
import matplotlib.pyplot as plt
import numpy as np


scope = cw.scope()
target = cw.target(scope, cw.targets.SimpleSerial)
scope.adc.samples = 100000


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
    return response, trace


# simpleserial_addcmd('a', 30, check_arr);
def check_arr(arr):
    scope.arm()
    target.simpleserial_write('a', bytes(arr))
    timeout = scope.capture()
    if timeout:
        raise RuntimeError("Capture timed out.")
    response = target.simpleserial_read('r', 20)
    trace = scope.get_last_trace()
    return response, trace


def get_trace_for_value(value):
    low, high = struct.pack('<H', value)
    pt = [0, low, high, 0]
    _ = reset()
    _, trace = get_pt(pt)
    return trace


def compute_transition_score(trace1, trace2):
    return np.sum(np.abs(trace2 - trace1))


def true_binary_search(low=0, high=2**16-1):
    while (high - low) > 1:
        mid = (low + high) // 2
        
        trace_low = get_trace_for_value(low)
        trace_mid = get_trace_for_value(mid)
        trace_high = get_trace_for_value(high)
        
        diff_low_mid = compute_transition_score(trace_low, trace_mid)
        diff_mid_high = compute_transition_score(trace_mid, trace_high)

        print(f"  [{low:5d}, {high:5d}] - [{diff_low_mid:.3f}, {diff_mid_high:.3f}]")

        if diff_low_mid > diff_mid_high:
            high = mid
        else:
            low = mid
    return low


def main():
    reset_target()

    found = [64986, 58772, 42349, 36080]
    recovered_array = []

    for i in range(len(found)-1):
        low = found[i+1] + 1
        high = found[i]  - 1
        value = true_binary_search(low=low, high=high)
        high = value - 1
        recovered_array.append(value)
        print(recovered_array)
    print(recovered_array)


if __name__ == "__main__":
    main()
