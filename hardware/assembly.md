# Assembly

No soldering if the eInk FeatherWing already has socket headers.

1. Update CircuitPython from [circuitpython.org](https://circuitpython.org/downloads?q=unexpected+maker+feathers3) if the shipping build is old. In the REPL, `dir(board)` should include `I2C2`, `LDO2`, and `D9`.
2. Plug the **100 mm** STEMMA cable into **I2C2** (the jack nearer USB) **before** stacking the wing. I2C2 is not on the long header.
3. Check LiPo polarity against the JST-PH silkscreen. Seat the 400 mAh cell in the header well. Use the wing’s normal-height sockets, not shorty headers.
4. Stack the eInk FeatherWing. Route the STEMMA cable out the side through the battery gap.
5. Leave the PMSA003I **beside** the stack with the fan vents open. Do not sandwich it.
6. First power-on from a USB-C **data** cable, battery connected.

Then copy `firmware/bringup.py` to `CIRCUITPY/code.py` and watch the serial console:

- I2C1 should list `0x36` (MAX17048)
- I2C2 should list `0x12` (PMSA003I)

Charge only via the Feather. Do not leave charging unattended for long. Do not puncture or bend the LiPo.

A 3D-printed two-piece case (USB hole, battery corral, display window, vented sensor bay) is in [enclosure/](enclosure/).
