import struct
import time
import random
import glob
import os

import chipwhisperer as cw
import matplotlib.pyplot as plt
import numpy as np


scope = cw.scope()
target = cw.target(scope, cw.targets.SimpleSerial)
scope.adc.samples = 4500


def reset_target():
    scope.io.nrst = 'low'
    time.sleep(0.05)
    scope.io.nrst = 'high_z'
    time.sleep(0.05)


# simpleserial_addcmd('e', 8, encrypt);
def encrypt(data):
    scope.arm()
    target.simpleserial_write('e', data)

    timeout = scope.capture()
    if timeout:
        raise RuntimeError("Capture timed out.")

    response = target.simpleserial_read('r', 8)
    trace = scope.get_last_trace()
    return response, trace


# simpleserial_addcmd('c', 16, verify);
def verify(key):
    target.simpleserial_write('c', bytes(key))
    response = target.simpleserial_read('r', 17)
    return response


def stack_trim(list_of_vecs):
    L = min(v.size for v in list_of_vecs)
    return np.vstack([v.ravel()[:L] for v in list_of_vecs])


def get_average_trace(data, repeats):
    traces = []
    for _ in range(repeats):
        response, trace = encrypt(data)
        traces.append(np.ravel(trace))

    array = stack_trim(traces)
    average = array.mean(axis=0)
    return average


def get_average_traces(repeats, key=None):
    traces = []
    for i in range(256):
        data = bytes([i for _ in range(8)])
        if key:
            data = bytes([data[j]^key[j] for j in range(8)])
        traces.append(get_average_trace(data, repeats))
    return traces


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


def store_traces(traces, path):
    for i, trace in enumerate(traces):
        np.save(f"traces/{path}/npy/{i}.npy", trace)
        plt.figure(figsize=(12,4))
        plt.plot(trace, label="trace")
        plt.axhline(0, color="k", linewidth=0.5)
        plt.legend()
        plt.title(f"Trace for: '{i}'")
        plt.xlabel("Sample index")
        plt.ylabel("Voltage (a.u.)")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f"traces/{path}/graphs/{i}.png", dpi=300)
        plt.close()


def get_dpas(traces, key=None, first=60, step=204):
    dpas = []
    for guess_bit in range(8):
        guess = [1<<guess_bit for _ in range(8)]
        ones = [[] for _ in range(8)]
        zeros = [[] for _ in range(8)]
        for pt_byte in range(256):
            pt = [pt_byte for _ in range(8)]
            result = [pt[i]^guess[i] for i in range(8)]

            if key:
                result = [result[i]^key[i] for i in range(8)]

            lsbs = [(b>>guess_bit) & 1 for b in result]
            for i, lsb in enumerate(lsbs):
                bit_offset = first + i*step

                start = bit_offset - 50
                end = bit_offset + 50

                if lsb:
                    ones[i].append(traces[pt_byte][start:end])
                else:
                    zeros[i].append(traces[pt_byte][start:end])

        for i in range(8):
            xor1_arr = stack_trim(ones[i])
            mean_xor1 = xor1_arr.mean(axis=0)
            xor0_arr = stack_trim(zeros[i])
            mean_xor0 = xor0_arr.mean(axis=0)

            dpa_diff = mean_xor1 - mean_xor0
            dpas.append(dpa_diff)
    return dpas


def main():
    repeats = 50
    path = "actual-challenge-pts"
    # traces = get_average_traces(repeats)
    # print("got traces")
    # store_traces(traces, path)
    traces = parse_traces(path)

    path = "actual-challenge-first-dpas"
    # dpas = get_dpas(traces, first=60, step=203)
    # print("got first dpas")
    # store_traces(dpas, path)
    dpas = parse_traces(path)

    # This must be derived from the above dpas
    key = [78, 97, 74, 45, 85, 103, 82, 100]

    path = "actual-challenge-second-dpas"
    # dpas = get_dpas(traces, first=1685, step=204, key=key)
    # print("got second dpas")
    # store_traces(dpas, path)
    dpas = parse_traces(path)

    # This must be derived from the above dpas
    key += [50, 112, 88, 107, 56, 118, 53, 115]

    response = verify(key)
    print(response)


if __name__ == "__main__":
    main()
