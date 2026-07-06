# meta-evb-ma35: OpenBMC BSP Layer for Nuvoton MA35 Family

OpenBMC Board Support Package for the Nuvoton MA35 Family evaluation boards.

## Supported Machines

| Machine | Board | SoC |
|---------|-------|-----|
| `numaker-iot-ma35d0` | NuMaker-IoT-MA35D03F80 | MA35D0 (dual Cortex-A35 @ 650 MHz) |
| `numaker-iot-ma35d05ki1` | NuMaker-IoT-MA35D05KI1 | MA35D05K (dual Cortex-A35 @ 650 MHz) |

## Hardware Specifications

| Item | Detail |
|------|--------|
| RAM | 256 MB DDR3L |
| Flash | 512 MB SPI NAND |
| Kernel | Linux 6.6.93 (arm64) |
| RootFS | UBI/UBIFS on SPI NAND |
| Serial Console | ttyS0, 115200 8N1 |
| Boot Flow | SPI NAND → TF-A BL2 → BL31 → U-Boot → Linux → OpenBMC |

## Build

```bash
# MA35D05K
MACHINE=numaker-iot-ma35d05ki1 source setup numaker-iot-ma35d05ki1 build-ma35d05k
bitbake nuwriter-pack

# MA35D0
MACHINE=numaker-iot-ma35d0 source setup numaker-iot-ma35d0 build-ma35d0
bitbake nuwriter-pack
```

## Layer Dependencies

- meta-numaker (parent layer)
- meta-arm

## Layer Structure

```
meta-evb-ma35/
├── conf/
│   ├── layer.conf
│   ├── machine/
│   │   ├── include/ma35-common.inc   ← shared SoC settings
│   │   ├── numaker-iot-ma35d0.conf
│   │   └── numaker-iot-ma35d05ki1.conf
│   └── templates/default/
├── recipes-bsp/
│   ├── tf-a/
│   │   ├── tf-a-ma35.inc             ← shared TF-A logic
│   │   ├── tf-a-ma35d0_2.3.bb        ← thin wrapper
│   │   ├── tf-a-ma35d05k_2.3.bb      ← thin wrapper
│   │   └── files/                     ← DDR headers
│   └── u-boot/
│       ├── u-boot-ma35.inc            ← shared U-Boot logic
│       ├── u-boot-ma35d0_2020.07.bb
│       └── u-boot-ma35d05k_2020.07.bb
├── recipes-devtools/python/
│   ├── nuwriter-pack.inc              ← shared NuWriter logic
│   ├── nuwriter-pack_1.0.bb
│   └── files/
├── recipes-kernel/linux/
│   ├── linux-ma35.inc                 ← shared kernel logic
│   ├── linux-ma35d0_6.6.93.bb
│   ├── linux-ma35d05k_6.6.93.bb
│   └── files/                         ← defconfigs, DTS, patches
├── recipes-nuvoton/packagegroups/
│   └── packagegroup-ma35-apps.bb      ← unified packagegroup
└── recipes-phosphor/entity-manager/
    ├── entity-manager_%.bbappend      ← uses ${MACHINE}.json
    └── entity-manager/
        ├── numaker-iot-ma35d0.json
        └── numaker-iot-ma35d05ki1.json
```
