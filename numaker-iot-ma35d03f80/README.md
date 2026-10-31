# NuMaker-IoT-MA35D03F80 V1.1

[Power-on guide](index.html) | [Interactive BOM](bom/ibom.html) | [Settings source](POWER_ON_SETTING.txt)

## Hardware Notes

- CON1 is USB-C 5V power; CON3 is Micro-USB USB0/NuWriter; CON9 is Micro-USB VCOM.
- SD1 is the full-size SD slot CON32. The microSD slot CON34 is SD0.
- J63 pins 1-2 must be shorted for RS-232 SOL according to the supplied settings.
- SD 8-bit is explicitly not supported in the supplied settings.
- The board title is MA35D03F80; the supplied BOM names the MCU MA35D03F864C.
  Confirm the mounted chip before device-specific use.

## Source Limitations

The board data contains 615 footprints, 2,046 pads and 479 nets. The supplied
BOM matches 575 references, but J14's footprint name differs. 574 values were
applied; 41 values remain blank instead of guessed. The BOM's History edits
are not automatically applied, and assembly-only rows are not PCB components.
BOM values take precedence over ASCII properties; crystal source strings differ.

The front/back views use Gerber solder-mask openings and silkscreen with 1,823
verified SMD pad centers. Drill holes are schematic PADS geometry. These pages
are assembly/location aids, not manufacturing, DRC or physical-hardware
certification. Power-off before changing switches or jumpers and verify I/O
voltage/device requirements before flashing.