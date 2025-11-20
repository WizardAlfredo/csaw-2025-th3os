import time

import chipwhisperer as cw
import chipwhisperer.common.results.glitch as glitch


scope = cw.scope()
scope.default_setup()
target = cw.target(scope, cw.targets.SimpleSerial)


def reboot_flush():
    scope.io.nrst = False
    time.sleep(0.05)
    scope.io.nrst = "high_z"
    time.sleep(0.05)
    target.flush()


def get_reference():
    target.simpleserial_write("d", b"")
    reference = target.simpleserial_read_witherrors('r', 26)['full_response']
    return reference


def main():
    gc = glitch.GlitchController(groups=["success", "reset", "normal"], parameters=["repeat", "ext_offset"])

    g_step = 1
    gc.set_global_step(g_step)
    gc.set_range("repeat", 12, 12)
    gc.set_range("ext_offset", 1400, 1600)
    gc.set_global_step(1)

    reboot_flush()

    sample_size = 1
    scope.glitch.repeat = 1
    broken = False
     
    reference = get_reference()
    print(f"Reference: {reference}")

    for glitch_settings in gc.glitch_values():
        scope.glitch.repeat = glitch_settings[0]
        scope.glitch.ext_offset = glitch_settings[1]

        print(glitch_settings)

        if broken:
            break
        for i in range(5):
            scope.arm()
            target.simpleserial_write("d", b"")
            ret = scope.capture()
            val = target.simpleserial_read_witherrors('r', 26, glitch_timeout=10)
            print(val)
            
            if ret:
                print('Timeout - no trigger')
                gc.add("reset", (scope.glitch.repeat, scope.glitch.ext_offset))
                reboot_flush()
            else:
                if val['valid'] is False:
                    gc.add("reset", (scope.glitch.repeat, scope.glitch.ext_offset))
                    reboot_flush()
                else:
                    if val['full_response'] != reference: 
                        broken = True
                        gc.add("success", (scope.glitch.repeat, scope.glitch.ext_offset))
                        print(val['full_response'], bytearray.fromhex(val['full_response'].strip()[1:]).decode() )
                        print(scope.glitch.repeat, scope.glitch.ext_offset)
                        break
                    else:
                        gc.add("normal", (scope.glitch.repeat, scope.glitch.ext_offset))


if __name__ == "__main__":
    main()
