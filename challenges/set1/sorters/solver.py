import chipwhisperer as cw
import numpy as np
import time
import struct

scope = cw.scope()
target = cw.target(scope, cw.targets.SimpleSerial)

cache = {}


def reset():
    target.simpleserial_write('x', b"")
    response = target.simpleserial_read('r', 1)
    return response


def num_q():
    target.simpleserial_write('q', b"0")
    response = target.simpleserial_read('r', 4)
    return struct.unpack("<I", response)[0]


def get_pt(pt):
    target.simpleserial_write('p', bytes(pt))
    response = target.simpleserial_read('r', 2)
    return response


def sort_data(i):
    scope.arm()
    cmd = 'c' if i == 1 else 'd'
    target.simpleserial_write(cmd, b"")
    timeout = scope.capture()
    if timeout:
        raise RuntimeError("Timeout")
    response = target.simpleserial_read('r', 1)
    trace = scope.get_last_trace()
    return trace


def check_array(arr, i):
    cmd = 'a' if i == 1 else 'b'
    bytes_arr = []
    for val in arr:
        bytes_arr.append(val & 0xFF)
        if i == 2:
            bytes_arr.append((val >> 8) & 0xFF)
    target.simpleserial_write(cmd, bytes(bytes_arr))
    response = target.simpleserial_read('r', 20)
    return response


def get_trace(value, position, i):
    key = (value, position, i)
    if key in cache:
        return cache[key]
    else:
        low = value & 0xFF
        high = (value >> 8) & 0xFF
        pt = [i, low, high, position]
        reset()
        get_pt(pt)
        trace = sort_data(i)
        t = trace[:700]
        cache[key] = t
        return t


def binary_search(position, high, i):
    low = 0
    while (high - low) > 1:
        mid = (low + high) // 2
        trace_low = get_trace(low, position, i)
        trace_mid = get_trace(mid, position, i)
        trace_high = get_trace(high, position, i)
        diff_low_mid = np.sum(np.abs(trace_mid - trace_low))
        diff_mid_high = np.sum(np.abs(trace_high - trace_mid))
        
        if diff_low_mid > diff_mid_high:
            high = mid
        else:
            low = mid
    return low


def solve_array(i):
    print(f"Solving for array {i}")
    recovered_array = []
    queries_before = num_q()
    high = (2**8-1) if i == 1 else (2**16-1)
    for position in [i for i in range(14, -1, -1)]:
        value = binary_search(position, high, i)
        recovered_array.append(value)
        high = value - 1
    
    recovered_array = recovered_array[::-1]
    response = check_array(recovered_array, i)
    
    if response:
        decoded = response.decode('utf-8', errors='ignore')
        print(f"Flag: {decoded}") 
        print(f"Array: {recovered_array}")
    queries_after = num_q()
    print(f"Total Queries: {queries_after - queries_before}\n\n")


def main():
    solve_array(1)
    solve_array(2)

    scope.dis()
    target.dis()
    

if __name__ == "__main__":
    main()
