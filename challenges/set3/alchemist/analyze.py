import struct
import time
import random
import glob
import os

import chipwhisperer as cw
import matplotlib.pyplot as plt
import numpy as np


def simplify(trace):
    new_trace = []
    for number in trace:
        if 0 <= number < 0.0015:
            new_trace.append(0)
        elif 0.0015 <= number < 0.0025:
            new_trace.append(1)
        elif 0.0025 <= number < 0.005:
            new_trace.append(2)
        elif 0.005 <= number < 0.015:
            new_trace.append(3)
        elif number >= 0.015:
            new_trace.append(4)

        if 0 >= number > -0.0015:
            new_trace.append(0)
        elif -0.0015 >= number > -0.0025:
            new_trace.append(-1)
        elif -0.0025 >= number > -0.005:
            new_trace.append(-2)
        elif -0.005 >= number < -0.015:
            new_trace.append(-3)
        elif number <= -0.015:
            new_trace.append(-4)
    return np.ravel(new_trace)


def store_traces(traces, path):
    for i, trace in enumerate(traces):
        start = 0
        step = 4000
        trace = trace[start:start+step]
        np.save(f"traces/{path}/npy/{i}.npy", trace)
        plt.figure(figsize=(12,4))
        plt.plot(trace, label="trace")
        plt.axhline(0, color="k", linewidth=0.5)
        plt.legend()
        plt.title(f"Trace for: '{i}'")
        plt.grid('on')
        plt.xlabel("Sample index")
        # plt.xticks(np.arange(1969, 4000, 303))
        plt.xticks(np.arange(60, 4000, 203))
        plt.ylabel("Voltage (a.u.)")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f"traces/{path}/graphs/{i}.png", dpi=500)
        plt.close()


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
    # path = "actual-challenge-dpas"
    # path = "first-block-pts"
    path = "actual-challenge-pts"
    traces = parse_traces(path)

    path = "analysis"
    store_traces(traces, path)


if __name__ == "__main__":
    main()  
