#!/usr/bin/env python3
import chipwhisperer as cw
import argparse
import time 


def reset_target(scope): 
    scope.io.nrst = 'low'
    time.sleep(0.05)
    scope.io.nrst = 'high_z'
    time.sleep(0.05)


def load_firmware(path):
    print(f"Loading firmware: {path}")
    scope = cw.scope()
    target = cw.target(scope, cw.targets.SimpleSerial)
    scope.default_setup()
    cw.program_target(scope, cw.programmers.STM32FProgrammer, path)


def main():
    print(f"Firmware loader.")
    parser = argparse.ArgumentParser(description="Firmware loader..")
    parser.add_argument("-f","--firmware", help="fimware file path", required=True)
    args = parser.parse_args()
    load_firmware(args.firmware)


if __name__ == '__main__':
    main()
