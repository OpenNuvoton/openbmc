# NuMaker-IoT-MA35D05KI1 V1.0

[Power-on guide](index.html) | [Interactive BOM](bom/ibom.html) | [Settings source](POWER_ON_SETTING.txt)

## Hardware Notes

- CON1 is USB-C 5V power; CON5 is Micro-USB USB0/NuWriter.
- U4 is RJ45; CON4 is the back-side microSD SD1 slot; SW2 is the six-position DIP.
- The settings text's Micro-USB VCOM description could not be matched to an
  independent USB-UART bridge in this board's data. The guide marks VCOM
  connection information as unverified rather than assigning a wrong port.

## Source Limitations

The board contains 297 footprints, 921 pads and 198 nets. Only X2 and X3 have
explicit ASCII values (12MHz); the other 295 values are blank and not grouped
as interchangeable parts. Footprint names are not electrical values.

The views are generated from verified PADS geometry using InteractiveHtmlBom.
Internal copper, pours and vias are omitted; outlines/fonts are approximated.
Four extraneous Chili source annotations were excluded. These are location
aids, not manufacturing, DRC or physical-hardware certification. Verify missing
values before purchasing or assembling, and power-off before changing switches.