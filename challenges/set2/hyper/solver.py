import time
import glob
import os

import chipwhisperer as cw
import matplotlib.pyplot as plt
import numpy as np

scope = cw.scope()
target = cw.target(scope, cw.targets.SimpleSerial)
scope.default_setup()
scope.adc.samples = 2200

REPEATS_GLOBAL = 5

def reset_target():
    scope.io.nrst = 'low'
    time.sleep(0.05)
    scope.io.nrst = 'high_z'
    time.sleep(0.05)


# simpleserial_addcmd('a', 12, arm_system);
def arm_system(sequence):
    target.simpleserial_write('a', sequence)
    response = target.simpleserial_read('r', 17)
    return response


# simpleserial_addcmd('p', 1, invert_polarity);
def invert_polarity(mask):
    scope.arm()
    target.simpleserial_write('p', bytes([mask]))

    timeout = scope.capture()
    if timeout:
        raise RuntimeError("Capture timed out.")

    response = target.simpleserial_read('r', 1)
    trace = scope.get_last_trace()
    return response, trace


def stack_trim(list_of_vecs):
    L = min(v.size for v in list_of_vecs)
    return np.vstack([v.ravel()[:L] for v in list_of_vecs])


def store_traces(traces, path):
    for i, trace in enumerate(traces):
        np.save(f"traces/{path}/npy/{i}.npy", trace)


def parse_traces(path):
    traces_path = f"traces/{path}/npy/"
    fs = [(int(os.path.splitext(os.path.basename(f))[0]), f) for f in glob.glob(os.path.join(traces_path, '*.npy'))]
    m = max(i for i,_ in fs)
    fs.sort()
    t0 = np.load(fs[0][1])

    traces = np.zeros((m+1, t0.shape[0]), dtype=t0.dtype)
    for i,f in fs: 
        traces[i] = np.load(f)

    return traces


def get_average_trace(mask, repeats):
    traces = []
    for _ in range(repeats):
        response, trace = invert_polarity(mask)
        traces.append(np.ravel(trace))

    array = stack_trim(traces)
    average = array.mean(axis=0)
    return average


def get_traces():
    traces = []
    repeats = REPEATS_GLOBAL
    for mask in range(256):
        print(mask)
        average = get_average_trace(mask, repeats)
        traces.append(average)
    return traces


def get_dpas(traces):
    dpas = []
    for i in range(8):
        ones = []
        zeros = []
        key_guess = 1 << i
        for pt in range(256):
            result = pt ^ key_guess
            lsb = result >> i & 1
            if lsb:
                ones.append(traces[pt])
            else:
                zeros.append(traces[pt])

        ones = stack_trim(ones)
        ones_average = ones.mean(axis=0)
        zeros = stack_trim(zeros)
        zeros_average = zeros.mean(axis=0)

        dpa = ones_average - zeros_average
        dpas.append(dpa)
    return dpas


def extract_bits(dpas, start, step):
    bits = ["" for _ in range(12)]
    for dpa in dpas:
        lsbs = []
        offset = start
        for _ in range(12):
            lsbs.append('1' if dpa[offset] > 0 else '0')
            offset += step
        for i, lsb in enumerate(lsbs):
            bits[i] += lsb
    
    return [int(_byte[::-1], 2) for _byte in bits]


def main():
    reset_target()

    path = "pts"
    traces = get_traces()
    store_traces(traces, path)
    traces = parse_traces(path)

    path = "dpas"
    dpas = get_dpas(traces)
    store_traces(dpas, path)
    dpas = parse_traces(path)
    key = bytes(extract_bits(dpas, 24, 171))
    flag = arm_system(key).decode()
    print(f"Flag: {flag}")

if __name__ == "__main__":
    main()
