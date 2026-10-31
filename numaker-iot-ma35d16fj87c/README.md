# NuMaker-IoT-MA35D16FJ87C V1.1

[Power-on guide](index.html) | [Interactive BOM](bom/ibom.html) | [Settings source](POWER_ON_SETTING.txt)

## Hardware Notes

- Source board is MA35D16FJ0 V1.1; the BOM names MCU MA35D16FJ(I)87C.
- CON2 is USB-C 5V power; CON9 is USB-C VCOM; CON10 is USB-C USB0/NuWriter.
  This differs from the supplied text's Micro-USB cable wording.
- CON5 is back-side microSD SD1; CON6/CON7 are back-side RJ45 connectors.
- SW7 is the eight-position boot DIP; SW2 is reset.

## Source Limitations

All 646 board references match the supplied BOM. The pages contain 2,079 pads
and 461 nets, with 70 BOM NC/DNP/DNI components visible as Not fitted.
BOM values take precedence: X2/X3/X4/X5 list 24/25/25/12MHz respectively,
while their ASCII Value strings all say 12MHz. Verify source discrepancies
before purchasing or assembly.

Front/back views use Gerber mask/silk with 1,826 matched SMD pad centers;
drill holes are schematic PADS geometry. Presets follow the supplied text,
not independent TRM or physical-hardware certification. These are location/
assembly aids, not manufacturing or DRC data. Power-off before switch changes
and verify I/O voltage/device requirements before flashing.