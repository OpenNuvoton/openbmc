# meta-numaker

OpenBMC BSP layer collection for Nuvoton NuMaker platforms.

## Directory Structure

```
meta-numaker/
├── conf/            # Layer configuration (numaker-layer)
├── doc/             # Docker build environment, board quickstarts, and test guides
├── meta-evb-ma35/   # Sub-layer for MA35 series EVBs (MA35D16, MA35D03, MA35D05K)
└── meta-evb-nuc980/ # Sub-layer for NUC980 series EVBs (NUC980G2)
```

- **[meta-evb-ma35](meta-evb-ma35/README.md)**: Machine configurations and recipes for 64-bit Cortex-A35 EVBs.
- **[meta-evb-nuc980](meta-evb-nuc980/README.md)**: Machine configurations and recipes for 32-bit ARM926EJ-S EVBs.
- **[doc](doc/)**: Docker build scripts, hardware setup, and feature test procedures.
