import time
import glob
import os
import struct

import chipwhisperer as cw
import matplotlib.pyplot as plt
import numpy as np

from salsa_z3_solver import extract_key


scope = cw.scope()
scope.default_setup()
scope.adc.samples = 200
target = cw.target(scope, cw.targets.SimpleSerial)


def reset_target(scope):
    scope.io.nrst = 'low'
    time.sleep(0.05)
    scope.io.nrst = 'high_z'
    time.sleep(0.05)


# // simpleserial_addcmd('s', 6, shift);
def _shift(threshold, shifts):
    scope.arm()
    data = bytes(threshold + shifts)
    target.simpleserial_write('s', data)

    timeout = scope.capture()
    if timeout:
        raise RuntimeError("Capture timed out.")

    response = target.simpleserial_read('r', 1)
    trace = scope.get_last_trace()
    return response, trace


# // simpleserial_addcmd('d', 16, decrypt);
def decrypt(key):
    data = bytes(key)
    timeout = target.simpleserial_write('d', data)
    if timeout:
        raise RuntimeError("Capture timed out.")
    response = target.simpleserial_read('r', 21)
    return response


def stack_trim(list_of_vecs):
    L = min(v.size for v in list_of_vecs)
    return np.vstack([v.ravel()[:L] for v in list_of_vecs])


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


def get_average_trace(threshold, shifts, repeats):
    traces = []
    for _ in range(repeats):
        response, trace = _shift(threshold, shifts)
        traces.append(np.ravel(trace))

    array = stack_trim(traces)
    average = array.mean(axis=0)
    return average


def get_reference_trace(threshold):
    shifts = [0, 0, 0, 0]
    repeats = 1
    reference_trace = get_average_trace(threshold, shifts, repeats)
    return reference_trace


def get_traces():
    repeats = 1
    threshold = [1, 0] # lsb, msb

    traces = []
    reference_traces = []
    # If you take 150 random shifts z3 will find only one possible key with very high probability.
    # selected_shifts = [[15, 1, 4, 13], [5, 12, 10, 12], [12, 11, 8, 14], [9, 13, 8, 10], [9, 4, 10, 8], [15, 15, 4, 11], [13, 14, 11, 4], [9, 4, 1, 14], [9, 13, 4, 11], [5, 6, 7, 3], [1, 5, 7, 1], [15, 13, 6, 12], [10, 15, 1, 11], [5, 14, 4, 9], [9, 7, 3, 12], [1, 10, 6, 15], [8, 9, 1, 15], [12, 5, 7, 14], [10, 8, 10, 2], [4, 12, 13, 1], [2, 11, 4, 13], [5, 5, 7, 3], [5, 2, 6, 3], [8, 3, 15, 1], [14, 15, 1, 11], [9, 7, 4, 9], [13, 11, 14, 5], [10, 15, 12, 2], [7, 10, 15, 15], [2, 8, 15, 6], [5, 14, 5, 14], [9, 9, 12, 1], [15, 3, 6, 7], [8, 1, 7, 9], [14, 2, 15, 13], [4, 10, 11, 3], [14, 15, 8, 7], [11, 12, 12, 2], [8, 10, 2, 4], [5, 10, 9, 10], [11, 8, 10, 2], [2, 8, 3, 13], [8, 4, 12, 14], [4, 10, 12, 13], [10, 1, 13, 9], [6, 7, 7, 8], [11, 5, 2, 7], [11, 15, 3, 10], [3, 2, 14, 5], [7, 11, 12, 5], [14, 8, 9, 13], [7, 14, 9, 10], [10, 4, 9, 15], [6, 10, 8, 7], [3, 1, 3, 14], [3, 11, 9, 3], [2, 2, 9, 15], [3, 15, 13, 7], [10, 8, 12, 4], [10, 11, 11, 9], [9, 3, 15, 8], [13, 11, 7, 15], [2, 8, 6, 2], [8, 4, 3, 3], [6, 15, 7, 8], [4, 9, 3, 12], [11, 10, 7, 7], [15, 15, 9, 9], [1, 9, 15, 8], [2, 11, 8, 7], [14, 14, 15, 7], [11, 10, 6, 7], [6, 2, 5, 9], [12, 15, 13, 14], [9, 14, 15, 5], [14, 14, 7, 15], [11, 2, 8, 12], [10, 3, 7, 1], [10, 6, 1, 15], [7, 6, 15, 10], [7, 2, 5, 8], [14, 2, 13, 12], [12, 8, 1, 5], [7, 11, 8, 10], [9, 1, 13, 9], [5, 11, 12, 9], [6, 9, 15, 12], [11, 7, 4, 6], [9, 9, 9, 13], [1, 2, 15, 14], [12, 3, 3, 3], [4, 2, 12, 5], [7, 1, 12, 8], [10, 2, 11, 13], [6, 8, 9, 9], [3, 3, 13, 2], [5, 7, 10, 4], [13, 12, 6, 13], [13, 10, 5, 6], [5, 7, 9, 1], [12, 2, 7, 3], [4, 9, 13, 1], [11, 7, 13, 3], [12, 5, 4, 3], [3, 8, 11, 10], [11, 2, 3, 12], [12, 3, 7, 11], [7, 14, 6, 4], [2, 3, 12, 7], [14, 4, 11, 5], [14, 12, 7, 3], [13, 2, 12, 13], [15, 4, 5, 7], [12, 14, 7, 6], [6, 12, 8, 11], [4, 12, 7, 14], [2, 15, 6, 8], [6, 4, 12, 5], [13, 14, 9, 14], [11, 12, 6, 5], [7, 2, 13, 2], [7, 3, 8, 8], [12, 9, 8, 9], [7, 5, 8, 6], [1, 5, 12, 4], [15, 13, 15, 10], [5, 1, 11, 7], [9, 4, 2, 14], [3, 6, 15, 8], [7, 3, 2, 10], [14, 8, 2, 8], [7, 13, 2, 13], [9, 11, 9, 8], [6, 10, 11, 7], [1, 6, 14, 4], [13, 1, 2, 4], [14, 15, 13, 6], [14, 5, 10, 3], [4, 3, 3, 7], [3, 14, 10, 7], [14, 2, 1, 12], [5, 1, 2, 13], [14, 7, 1, 12], [3, 3, 7, 14], [6, 15, 13, 9], [15, 2, 8, 7], [14, 11, 9, 13], [8, 1, 13, 5], [12, 7, 14, 1], [15, 11, 3, 14]]
    selected_shifts = [[5, 7, 9, 1], [3, 11, 9, 3], [12, 8, 1, 5], [8, 9, 1, 15], [7, 14, 6, 4], [7, 2, 5, 8], [1, 5, 7, 1], [11, 8, 10, 2], [14, 15, 1, 11], [5, 2, 6, 3], [3, 2, 14, 5], [9, 4, 1, 14], [4, 12, 13, 1], [8, 3, 15, 1], [9, 9, 12, 1], [12, 2, 7, 3], [10, 6, 1, 15], [4, 9, 13, 1], [10, 15, 12, 2], [12, 15, 13, 14], [5, 6, 7, 3], [5, 14, 5, 14], [8, 1, 7, 9], [10, 3, 7, 1], [10, 15, 1, 11], [15, 15, 4, 11], [8, 4, 3, 3], [12, 3, 3, 3], [11, 12, 12, 2], [8, 10, 2, 4]]

    for i in range(1, 17):
        threshold = [i, 0]
        reference_trace = get_reference_trace(threshold)
        reference_traces.append(reference_trace)

    for num, shifts in enumerate(selected_shifts):
        print(num)
        for i in range(1, 17):
            threshold = [i, 0]
            trace = get_average_trace(threshold, shifts, repeats)
            traces.append(trace)
    return traces, reference_traces


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


def main():
    # traces, reference_traces = get_traces()

    path = "oracle"
    # store_traces(traces, path)
    traces = parse_traces(path)

    path = "reference"
    # store_traces(reference_traces, path)
    reference_traces = parse_traces(path)

    branches = []
    for i, trace in enumerate(traces):
        correlation = np.corrcoef(trace, reference_traces[i%16])[0, 1]
        if correlation > 0.45:
            branches.append(0)
            print(f"0, {correlation:.3f}")
        else:
            branches.append(1)
            print(f"1, {correlation:.3f}")

    with open("traces.txt", "w") as f:
        f.write('\n'.join([str(i) for i in branches]))

    key16 = extract_key()
    print(f"Found key: {key16}")

    key = []
    for i in key16:
        low, high = struct.pack('<H', i)
        key += [low, high]
    response = decrypt(key)
    print(f"Flag: {response.decode()}")



if __name__ == "__main__":
    main()
