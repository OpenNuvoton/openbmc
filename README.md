# OpenBMC for Nuvoton NuMaker Platforms

This repository is Nuvoton's OpenBMC distribution supporting the **NuMaker** evaluation boards. Built and operated within a Linux environment, it provides full Board Support Packages (BSP) integrated with the Yocto/OpenEmbedded build framework, the phosphor software stack, and advanced out-of-band server management features.

---

## 1. Quick Start: Build Environment Setup

### 1.1 Clone the Repository (Host)

On your host machine, clone the OpenBMC repository:

```bash
git clone https://github.com/OpenNuvoton/openbmc.git
```

Enter the cloned repository directory:

```bash
cd openbmc
```

---

### 1.2 Build & Enter Docker Environment (Host)

To ensure reproducible builds across diverse Linux distributions, use the preconfigured Ubuntu 24.04 Docker environment (detailed in [Docker Environment Guide](meta-numaker/doc/docker/README.md)).

---

## 2. Supported Boards & Build Guides

Once inside the Docker container (`~/openbmc`), select your evaluation board below for board-specific setup, Bitbake compilation commands, flashing, and verification:

| Evaluation Board | Order No. | Target Machine | Documentation |
| :--- | :--- | :--- | :--- |
| **NuMaker-IoT-MA35D16FJ0** | NK-IMA35D1A3 | `numaker-iot-ma35d16fj87c` | [Quickstart Guide](meta-numaker/doc/numaker-iot-ma35d16fj87c/README.md) |
| **NuMaker-IoT-MA35D03F80** | NK-IMA35D0A1 | `numaker-iot-ma35d03f80` | [Quickstart Guide](meta-numaker/doc/numaker-iot-ma35d03f80/README.md) |
| **NuMaker-IoT-MA35D05KI1** | NK-IMA35D0A2(Chili Pro) | `numaker-iot-ma35d05ki1` | [Quickstart Guide](meta-numaker/doc/numaker-iot-ma35d05ki1/README.md) |
| **NuMaker-IIoT-NUC980G2** | NK-980IOTG2 | `numaker-iot-nuc980g2` | [Quickstart Guide](meta-numaker/doc/numaker-iot-nuc980g2/README.md) |

---
