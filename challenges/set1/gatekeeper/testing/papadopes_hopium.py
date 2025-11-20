import chipwhisperer as cw
from string import ascii_lowercase, digits, ascii_uppercase
import time
from collections import Counter


scope = cw.scope()
target = cw.target(scope, cw.targets.SimpleSerial)
scope.default_setup()


def measure_response_time(password, n=30):
    times = []
    
    for _ in range(n):
        # Send and time response
        start = time.perf_counter()
        target.simpleserial_write('b', password)
        resp = target.simpleserial_read('r', 1)
        end = time.perf_counter()
        
        if resp is not None:
            elapsed = abs((end - start) * 1000000)
            print(f"DEBUG elapsed = {elapsed}")
            times.append(elapsed)
    
    if not times:
        return 0, 0
    
    import numpy as np
    return np.mean(times), np.std(times)


def find_char_response_timing(known_prefix, charset, num_runs=5):
    actual_pos = len(known_prefix) - 4
    print(f"\n[Pos {actual_pos}] After: '{known_prefix.decode()}'")
    
    # Expected delay at this position
    #delay_cycles = 2500 - (len(known_prefix) - 4) * 125
    #print(f"  Expected delay: {delay_cycles} cycles")
    
    #if delay_cycles < 800:
    #    print(f"  ⚠ Very weak signal (<800 cycles)")
    
    print(f"  Running {num_runs} aggregated measurements...")
    
    all_winners = []
    
    for run in range(num_runs):
        print(run)
        results = []
        
        for char in charset:
            test_pw = known_prefix + bytes([ord(char)]) + b'#' * (17 - len(known_prefix) - 2) + b'}'
            
            # Quick measurement (10 samples per char per run)
            mean_time, _ = measure_response_time(test_pw, n=3)
            results.append((char, mean_time))
        
        # Sort by time (longest = most delay = correct)
        results.sort(key=lambda x: x[1], reverse=True)
        winner = results[0][0]
        all_winners.append(winner)
        
        if (run + 1) % 5 == 0:
            print(f"    {run+1}/{num_runs}", end='\r')
    
    print()
    
    # Vote on winner
    counts = Counter(all_winners)
    top_votes = counts.most_common(10)
    
    print(f"  Voting results:")
    for i, (char, count) in enumerate(top_votes):
        pct = (count / num_runs) * 100
        marker = " ← WINNER" if i == 0 else ""
        print(f"    {i+1}. '{char}': {count}/{num_runs} ({pct:.1f}%){marker}")
    
    winner = top_votes[0][0]
    confidence = (top_votes[0][1] / num_runs) * 100
    
    if confidence < 15:
        print(f"  ⚠⚠⚠ Random ({confidence:.1f}%) - signal below noise!")
    elif confidence < 30:
        print(f"  ⚠ Low confidence ({confidence:.1f}%)")
    else:
        print(f"  ✓ Good confidence ({confidence:.1f}%)")
    
    return winner

# ============================================================================
# SOLVE LAST 6 CHARS
# ============================================================================

print("\n" + "="*70)
print("SOLVING LAST 6 CHARACTERS")
print("="*70)

gk2_password = b'gk2{7rU3ncr'
charset = ascii_lowercase + ascii_uppercase + digits

print(f"\nKnown: {gk2_password.decode()}")
print(f"Method: Response timing (bypasses ADC)")
print(f"Measurements: 10 runs × 10 samples × 63 chars = 6300/position")
print(f"Time: ~30 minutes\n")

for pos in range(6):
    next_char = find_char_response_timing(gk2_password, charset, num_runs=3)
    gk2_password += bytes([ord(next_char)])
    print(f"  → {gk2_password.decode()}\n")

gk2_password += b'}'

print(f"\n" + "="*70)
print(f"FINAL: {gk2_password.decode()}")
print("="*70)

# Verify
target.simpleserial_write('b', gk2_password)
resp = target.simpleserial_read('r', 1, timeout=500)

if resp and resp[0] == 1:
    print(f"\n✓✓✓ SUCCESS! Flag: {gk2_password.decode()}")
else:
    print(f"\nResponse: {resp}")
    print(f"\nIF ALL POSITIONS SHOW <15% CONFIDENCE:")
    print(f"GK2's signal (625-1250 cycles) is fundamentally too weak for CW Nano")
    print(f"This challenge likely requires CW-Lite/Pro hardware")

scope.dis()
target.dis()
