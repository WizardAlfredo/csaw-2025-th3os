import chipwhisperer as cw
import time
import threading

# --- CONFIG ------------------------------------------------
# Which TIO pin your target uses for trigger (0..3 for TIO1..TIO4)
TIO_INDEX = 3  # common: TIO4 -> index 3. Change if needed.

# The SimpleSerial command letter your target expects for the password:
# e.g. many challenges use 'b' or 'p'. Update to match your target firmware.
CMD_LETTER = 'b'

# Your password payload:
# Option A: bytes / bytearray (common)
password_bytes = bytearray(b"gk2{7rU3ncrYkIND}")   # <-- put your password here
# Option B: list of ints (e.g., [0x41, 0x42,...]) also works:
# password_bytes = bytearray([ord(c) for c in "my_secret"])

# -----------------------------------------------------------

scope = cw.scope()    # auto-detect (Nano)
# Create a SimpleSerial target instance (adjust if you use a custom target)
target = cw.target(scope, cw.targets.SimpleSerial)

# Set TIO pins to input (high_z) so we can read the physical line
scope.io.tio1 = "high_z"
scope.io.tio2 = "high_z"
scope.io.tio3 = "high_z"
scope.io.tio4 = "high_z"

# Helper to get pin state (returns 0 or 1)
def read_tio(idx):
    return scope.io.tio_states[idx]

# Polling thread: waits for rising edge then falling edge, records timestamps.
class TriggerPoller(threading.Thread):
    def __init__(self, tio_index):
        super().__init__()
        self.tio_index = tio_index
        self.t_rise = None
        self.t_fall = None
        self.finished = threading.Event()
        self.daemon = True

    def run(self):
        # Ensure we start when line idle (low)
        while read_tio(self.tio_index) != 0:
            pass
        # Wait for rising edge
        while read_tio(self.tio_index) == 0:
            pass
        self.t_rise = time.perf_counter()
        # Wait for falling edge
        while read_tio(self.tio_index) == 1:
            pass
        self.t_fall = time.perf_counter()
        self.finished.set()

# --- Run one measurement -----------------------------------
poller = TriggerPoller(TIO_INDEX)
poller.start()                       # start polling *before* sending command
time.sleep(0.000050)                 # tiny short gap to ensure poller is running (50 us)

# Send password to target (this triggers target code which will call trigger_high()/trigger_low())
target.simpleserial_write(CMD_LETTER, password_bytes)

# Optionally wait for ack/response from the target (depends on your target)
# If your firmware sends a response command letter, read it here (non-blocking variations exist).
# Example: wait for the poller to finish (falling edge observed)
poller.finished.wait(timeout=2.0)   # wait up to 2 seconds for the falling edge

if poller.t_rise is None or poller.t_fall is None:
    print("Warning: Trigger edges not captured (timed out or missed).")
else:
    dt = poller.t_fall - poller.t_rise
    print(f"Trigger HIGH duration: {dt*1e6:.3f} µs ({dt:.9f} s)")

# If your target returns an application-level response over simpleserial, read it now:
# Example: if target sends back 'r' with 1 byte you expected:
try:
    resp = target.simpleserial_read('r', 1, timeout=2)
    print("Target response:", resp)
except Exception as e:
    # Not all targets return; ignore if none expected
    print("No application-level simpleserial response or timed out:", e)
