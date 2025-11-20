from z3 import *


ROUNDS = 2
SHIFTS = (2, 7, 9, 13)
nonce = [0xeaee, 0x83a0, 0xd9a6, 0xb8f7]


def ROTL(a, b, trace=None):
    global z3key, solver
    if isinstance(a, int):
        if a >= (1 << (16 - b)):
            return ((a << b) | (a >> (16 - b))) & 0xffff
        else:
            return (a << b) & 0xffff
    else:
        if trace != None:
            if trace == 1:
                solver.add(simplify(UGE(a, (1 << (16 - b)))))
            elif trace == 0:
                solver.add(simplify(ULT(a, (1 << (16 - b)))))
        return ((a << b) | LShR(a, (16 - b)))


def QR(a, b, c, d, shifts):
    global z3key, solver, traces
    t0, t1, t2, t3 = traces[:4]
    traces = traces[4:]
    b ^= ROTL((a + d) & 0xffff, shifts[0], t0)
    c ^= ROTL((b + a) & 0xffff, shifts[1], t1)
    d ^= ROTL((c + b) & 0xffff, shifts[2], t2)
    a ^= ROTL((d + c) & 0xffff, shifts[3], t3)
    return a, b, c, d


def block(in_block, shifts, rounds):
    global z3key, solver
    x = in_block[:]
    for i in range(0, rounds):
        if i % 2 == 0:
            x[0] , x[4] , x[8] , x[12] = QR(x[0] , x[4] , x[8] , x[12], shifts)
            x[5] , x[9] , x[13], x[1]  = QR(x[5] , x[9] , x[13], x[1] , shifts)
            x[10], x[14], x[2] , x[6]  = QR(x[10], x[14], x[2] , x[6] , shifts)
            x[15], x[3] , x[7] , x[11] = QR(x[15], x[3] , x[7] , x[11], shifts)

        elif i % 2 == 1:
            x[0] , x[1] , x[2] , x[3]  = QR(x[0] , x[1] , x[2] , x[3] , shifts)
            x[5] , x[6] , x[7] , x[4]  = QR(x[5] , x[6] , x[7] , x[4] , shifts)
            x[10], x[11], x[8] , x[9]  = QR(x[10], x[11], x[8] , x[9] , shifts)
            x[15], x[12], x[13], x[14] = QR(x[15], x[12], x[13], x[14], shifts)
    out = [(x[i] + in_block[i]) for i in range(16)]
    return out


def shift(key, shifts=SHIFTS, rounds=ROUNDS):
    global z3key, solver
    assert len(key) == 8
    x = [0] * 16
    x[0]  = 0x4554
    x[1]  = key[0]
    x[2]  = key[1]
    x[3]  = key[2]
    x[4]  = key[3]
    x[5]  = 0x4332
    x[6]  = nonce[0]
    x[7]  = nonce[1]
    x[8]  = nonce[2]
    x[9]  = nonce[3]
    x[10] = 0x3032
    x[11] = key[4]
    x[12] = key[5]
    x[13] = key[6]
    x[14] = key[7]
    x[15] = 0x3520

    y = block(x, shifts, rounds)
    return y


def extract_key():
    global z3key, solver, traces

    traces_file = "traces.txt"
    traces = [int(bit) for bit in open(traces_file, "r").read().strip().split()]

    z3key = [BitVec(f"k_{i}", 16) for i in range(8)]
    solver = Solver()

    # selected_shifts = [(15, 1, 4, 13), (5, 12, 10, 12), (12, 11, 8, 14), (9, 13, 8, 10), (9, 4, 10, 8), (15, 15, 4, 11), (13, 14, 11, 4), (9, 4, 1, 14), (9, 13, 4, 11), (5, 6, 7, 3), (1, 5, 7, 1), (15, 13, 6, 12), (10, 15, 1, 11), (5, 14, 4, 9), (9, 7, 3, 12), (1, 10, 6, 15), (8, 9, 1, 15), (12, 5, 7, 14), (10, 8, 10, 2), (4, 12, 13, 1), (2, 11, 4, 13), (5, 5, 7, 3), (5, 2, 6, 3), (8, 3, 15, 1), (14, 15, 1, 11), (9, 7, 4, 9), (13, 11, 14, 5), (10, 15, 12, 2), (7, 10, 15, 15), (2, 8, 15, 6), (5, 14, 5, 14), (9, 9, 12, 1), (15, 3, 6, 7), (8, 1, 7, 9), (14, 2, 15, 13), (4, 10, 11, 3), (14, 15, 8, 7), (11, 12, 12, 2), (8, 10, 2, 4), (5, 10, 9, 10), (11, 8, 10, 2), (2, 8, 3, 13), (8, 4, 12, 14), (4, 10, 12, 13), (10, 1, 13, 9), (6, 7, 7, 8), (11, 5, 2, 7), (11, 15, 3, 10), (3, 2, 14, 5), (7, 11, 12, 5), (14, 8, 9, 13), (7, 14, 9, 10), (10, 4, 9, 15), (6, 10, 8, 7), (3, 1, 3, 14), (3, 11, 9, 3), (2, 2, 9, 15), (3, 15, 13, 7), (10, 8, 12, 4), (10, 11, 11, 9), (9, 3, 15, 8), (13, 11, 7, 15), (2, 8, 6, 2), (8, 4, 3, 3), (6, 15, 7, 8), (4, 9, 3, 12), (11, 10, 7, 7), (15, 15, 9, 9), (1, 9, 15, 8), (2, 11, 8, 7), (14, 14, 15, 7), (11, 10, 6, 7), (6, 2, 5, 9), (12, 15, 13, 14), (9, 14, 15, 5), (14, 14, 7, 15), (11, 2, 8, 12), (10, 3, 7, 1), (10, 6, 1, 15), (7, 6, 15, 10), (7, 2, 5, 8), (14, 2, 13, 12), (12, 8, 1, 5), (7, 11, 8, 10), (9, 1, 13, 9), (5, 11, 12, 9), (6, 9, 15, 12), (11, 7, 4, 6), (9, 9, 9, 13), (1, 2, 15, 14), (12, 3, 3, 3), (4, 2, 12, 5), (7, 1, 12, 8), (10, 2, 11, 13), (6, 8, 9, 9), (3, 3, 13, 2), (5, 7, 10, 4), (13, 12, 6, 13), (13, 10, 5, 6), (5, 7, 9, 1), (12, 2, 7, 3), (4, 9, 13, 1), (11, 7, 13, 3), (12, 5, 4, 3), (3, 8, 11, 10), (11, 2, 3, 12), (12, 3, 7, 11), (7, 14, 6, 4)]
    selected_shifts = [(5, 7, 9, 1), (3, 11, 9, 3), (12, 8, 1, 5), (8, 9, 1, 15), (7, 14, 6, 4), (7, 2, 5, 8), (1, 5, 7, 1), (11, 8, 10, 2), (14, 15, 1, 11), (5, 2, 6, 3), (3, 2, 14, 5), (9, 4, 1, 14), (4, 12, 13, 1), (8, 3, 15, 1), (9, 9, 12, 1), (12, 2, 7, 3), (10, 6, 1, 15), (4, 9, 13, 1), (10, 15, 12, 2), (12, 15, 13, 14), (5, 6, 7, 3), (5, 14, 5, 14), (8, 1, 7, 9), (10, 3, 7, 1), (10, 15, 1, 11), (15, 15, 4, 11), (8, 4, 3, 3), (12, 3, 3, 3), (11, 12, 12, 2), (8, 10, 2, 4)]
    for new_shifts in selected_shifts:
        shift(z3key, new_shifts, 1)

    while solver.check() == sat:
        model = solver.model()
        possible_key = [model.eval(zkey).as_long() for zkey in z3key]
        solver.add(Or(*[
            z3key[i] != possible_key[i] for i in range(8)
        ]))
    return possible_key
