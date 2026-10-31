# NuMaker-IIoT-NUC980G2 V1.1

[Power-on guide](index.html) | [Interactive BOM](bom/ibom.html) | [Supplied settings](POWER_ON_SETTING.txt)

## Hardware And Boot Conditions

- Shared G1/G2 artwork is V1.1; the supplied BOM specifies NUC980DK71YC.
  Verify the mounted chip/variant before hardware-specific use.
- CON9 is USB-C USB Device/NuWriter; CON4 is USB-C NUC123 VCOM/UART0.
  Both differ from the original settings text's Micro-USB wording.
- CON5 is front-side RJ45; CON8 is back-side microSD; U8 is SPI NAND; K3 is reset.
- SW1 has two bits, PG0/PG1. Supplied silkscreen gives ON=0 and OFF=1:
  both ON select USB Download, both OFF select QSPI Flash_0.
- QSPI selection alone does not certify SPI NAND boot. Back-side R26/PG8 and
  R27/PG9 solder pull-down options select the subtype; SPI NAND 1-bit requires
  both signals at 0. R26 has no BOM value/assembly record, while R27 is listed
  as 10K. Verify actual assembly before applying the SPI NAND run workflow.

The guide preserves the provided NuWriter GUI flow: Target SPI NAND, Erase
All/Erase, then Burn Type Pack with nuwriter-pack.bin. NuWriter and firmware
must be provided separately. Power-off before switch or solder changes.

## Data Limitations

The board contains 331 footprints, 1,169 pads and 279 nets. XLSX BOM has
288 references; 284 values were applied after footprint checks. 43 missing
records and four footprint-name disagreements (M1/D1/D2/F2) leave 47 values
unavailable instead of guessed. Three assembly-note rows are kept distinct
from PCB parts. X4 differs between ASCII (12MHz) and BOM (25MHz).

Gerber mask/silkscreen views matched all 998 sampled SMD pad centers.
Drill geometry/fonts and other board views are schematic assembly/location
aids, not manufacturing or DRC data. Switch positions supplement the original
text using the supplied board table, not independent TRM/physical-board
certification. Verify electrical/solder requirements and missing values before
flashing, purchasing or assembly.