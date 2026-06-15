# OpenBMC Docker Build Environment

You need these things to develop projects in the OpenBMC environment. A host system with a minimum of 50 GB of free disk space running a supported Linux distribution (i.e. recent releases of Fedora, CentOS, Debian, or Ubuntu), and appropriate packages installed on the system you are using for builds. Nuvoton provides two ways to set up the build environment: Docker and native Linux. Docker is based on the host Linux OS, so settings inside Docker won't affect the host OS and Docker can create an isolated environment only for building images. Since Linux distributions update frequently and may cause build errors, Docker is the recommended approach.

## Prerequisites

- Linux host (Ubuntu 20.04+ or other distros)
- Docker installed (`docker-ce`)
- Current user can run `sudo docker`

### Install Docker

Docker is an open-source project based on Linux containers. They are similar to virtual machines, but containers are more portable, more resource-friendly, and more dependent on the host operating system. Docker provides a quick and easy way to get up and running.

Install Docker on Ubuntu:

```bash
# Update package list
sudo apt-get update

# Install prerequisite packages for HTTPS
sudo apt install apt-transport-https ca-certificates curl software-properties-common

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# Add Docker repository
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

# Update package database with Docker packages
sudo apt-get update

# Install Docker
sudo apt-get install -y docker-ce docker-ce-cli containerd.io
```

Verify Docker is running:

```bash
sudo docker run hello-world
```

---

## Usage

### 1. Build Docker Image and Create Container

```bash
cd meta-numaker/doc/
./build.sh
```

This script will:
- Generate a Dockerfile using your current UID/username
- Build Docker image: `openbmc-numaker-<username>:v1`
- Create container: `openbmc-numaker_<username>`
- Mount `~/shared` as a shared directory inside the container

> If the image/container already exists, it will be skipped.

### 2. Enter the Container

```bash
./join.sh
```

You will see a prompt like:

```
username@container_id:~$
```

### 3. Build OpenBMC Inside the Container

```bash
# Enter shared directory
cd ~/shared

# Clone OpenBMC
git clone -b numaker https://github.com/OpenNuvoton/openbmc.git
cd openbmc

# Build NUC980
TEMPLATECONF=meta-numaker/meta-evb-nuc980/conf/templates/default \
  source oe-init-build-env build-nuc980
bitbake nuwriter-nuc980-pack

# Or build MA35D0
TEMPLATECONF=meta-numaker/meta-evb-ma35d0/conf/templates/default \
  source oe-init-build-env build-ma35d0
bitbake nuwriter-ma35d0-pack
```

---

## File Description

| File | Purpose |
|------|---------|
| `Dockerfile` | Docker image definition (Ubuntu 24.04 + Yocto dependencies) |
| `build.sh` | Build image and create container (auto-maps UID) |
| `join.sh` | Enter the existing container |

---

## Common Operations

```bash
# Check container status
sudo docker ps -a | grep openbmc-numaker

# Stop container
sudo docker stop openbmc-numaker_$(id -nu)

# Remove container (for rebuild)
sudo docker rm openbmc-numaker_$(id -nu)

# Remove image (for rebuild)
sudo docker rmi openbmc-numaker-$(id -nu):v1

# Rebuild (after removal)
./build.sh
```

---

## Notes

- `~/shared` is shared between host and container; build output should go here
- Container user UID matches host UID to avoid file permission issues
- First `bitbake` build takes a long time (~2-6 hours depending on network and host performance)
- Recommended minimum disk space: 50 GB
