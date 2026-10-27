# OpenBMC Docker Build Environment

Building OpenBMC with Yocto requires an isolated Linux environment with specific cross-compilation dependencies and toolchains. Because host Linux distributions update frequently and may introduce package version mismatches, Nuvoton provides a pre-configured Docker container environment based on **Ubuntu 24.04**.

Docker isolates the build environment from the host operating system while transparently mapping the host user's UID and home shared directory, completely avoiding file permission and ownership conflicts.

> [!NOTE]
> **Docker vs. Native Linux Build**:
> - **Docker (Recommended)**: Clean, reproducible, and pre-packaged with all required Bitbake and NuWriter Python dependencies. Settings inside Docker do not alter the host OS.
> - **Native Linux**: Requires installing build packages directly on the host using `apt-get`.

---

## 1. Prerequisites

- **Host Operating System**: 64-bit Ubuntu (Ubuntu 24.04).
- **Disk Space**: At least **50~100 GB** free space on the host disk (Yocto downloads upstream sources, builds cross-compilers, and stores `sstate-cache`).
- **RAM**: Minimum 16 GB (32 GB or more recommended for parallel Bitbake compilations).
- **Docker**: Docker Engine installed (`docker-ce` or `docker.io`).
- **User Permissions**: Current user must have `sudo` privileges to run Docker commands.

### Installing Docker on Ubuntu (24.04)

Use Docker's official modern installation method (using the new `keyrings` directory without deprecated `apt-key`):

1. Update package lists:
```bash
sudo apt-get update
```

Install basic tools:
```bash
sudo apt-get install -y ca-certificates curl gnupg lsb-release
```

2. Create keyrings directory:
```bash
sudo install -m 0755 -d /etc/apt/keyrings
```

Add Docker's official GPG key:
```bash
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
```

> [!TIP]
> If `curl` hangs (common in WSL2 or behind corporate network firewalls/proxies due to OCSP lookup timeouts), add `-k` (`--insecure`) to bypass TLS certificate verification:
> ```bash
> curl -k -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
> ```

Set key permissions:
```bash
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

3. Set up the Docker stable repository:
```bash
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

4. Update package lists:
```bash
sudo apt-get update
```

Install Docker Engine, CLI, and Containerd:
```bash
sudo apt-get install -y docker-ce docker-ce-cli containerd.io
```

5. Verify Docker installation:
```bash
sudo docker run --rm hello-world
```

---

## 2. Setting Up & Using the Container

### 2.1 Build Docker Image and Create Container

Navigate to the `docker` directory and run `build.sh`:

```bash
cd meta-numaker/doc/docker/
```

```bash
./build.sh
```

> [!WARNING]
> **Do NOT run `./build.sh` as `root` (or with `sudo ./build.sh`)**:
> `build.sh` automatically reads your regular user UID (`$(id -u)`) and username (`$(id -nu)`) to map container permissions. Running as `root` will abort with an error.

**What `build.sh` does automatically:**
1. Checks that the current user is not `root`.
2. Creates the shared workspace directory at `$HOME/shared` on the host (if not already existing).
3. Automatically detects your host OpenBMC repository and mounts it directly into `/home/<username>/openbmc`.
4. Copies `Dockerfile` to `Dockerfile_build` and modifies it to match your current host UID and username.
5. Builds the Docker image: `openbmc-numaker-<username>:v1`.
6. Creates the persistent container: `openbmc-numaker_<username>`, mounting both host `$HOME/shared` (to `~/shared`) and the repository (to `~/openbmc`).

### 2.2 Enter the Container

Whenever you want to enter the build container:

```bash
./join.sh
```

`join.sh` automatically enters the mounted OpenBMC repository directory:
```text
username@container_id:~/openbmc$
```

---

## 3. Working Inside the Container

When you enter the container via `./join.sh`, you are automatically located inside your mounted repository at `~/openbmc`:

```bash
cd ~/openbmc
```

> [!NOTE]
> **Zero Re-Cloning Needed!**
> The OpenBMC repository on your host machine is mounted directly into `/home/<username>/openbmc`.
> - Any code edits made on the host (e.g. via VS Code or your host IDE) are immediately visible inside the container.
> - All compilation outputs and deployed images (`build-*/tmp/deploy/images/`) reside directly on your host filesystem.
> - Additional persistent shared storage is also accessible at `~/shared` (mounted from host `$HOME/shared`).

> [!TIP]
> **Board-Specific Build Guides**:
> For step-by-step Bitbake commands and configuration instructions for each evaluation board, refer to the respective board documentation:
> - [NuMaker-IoT-NUC980G2 Guide](../numaker-iot-nuc980g2/README.md)
> - [NuMaker-IoT-MA35D03F80 Guide](../numaker-iot-ma35d03f80/README.md)
> - [NuMaker-IoT-MA35D05KI1 Guide](../numaker-iot-ma35d05ki1/README.md)
> - [NuMaker-IoT-MA35D16FJ87C Guide](../numaker-iot-ma35d16fj87c/README.md)

---

## 4. File Description

| File | Purpose |
| :--- | :--- |
| [`Dockerfile`](Dockerfile) | Base container definition: Ubuntu 24.04 with complete Yocto build packages, locale configuration, and NuWriter Python dependencies. |
| [`build.sh`](build.sh) | Automated build script: maps host UID/username, builds the Docker image, and creates the container with the shared folder mount. |
| [`join.sh`](join.sh) | Enters the running development container via `docker exec`. |
| [`destroy.sh`](destroy.sh) | Teardown script (orthogonal to `build.sh`): cleanly stops and removes the development container and image. |
| [`README.md`](README.md) | Documentation and operational guide for the Docker build environment. |

---

## 5. Container Management & Lifecycle

Check container status:
```bash
sudo docker ps -a | grep openbmc-numaker
```

Stop the container:
```bash
sudo docker stop openbmc-numaker_$(id -nu)
```

Restart / Start the container:
```bash
sudo docker start openbmc-numaker_$(id -nu)
```

One-click teardown (removes container and image):
```bash
./destroy.sh
```

Remove container only (preserves image for rapid recreate):
```bash
./destroy.sh -c
```

Full rebuild from scratch:
```bash
./build.sh
```

### 5.1 Troubleshooting Stuck Containers (ZFS Storage Driver)

On Ubuntu systems with ZFS root installations, Docker utilizes the `zfs` storage driver. If `./destroy.sh` encounters an error such as:
- `driver "zfs" failed to remove root filesystem: ... dataset does not exist`
- `driver "zfs" failed to remove root filesystem: ... filesystem has dependent clones`

The container will remain trapped in `Removal In Progress` or `Dead` state, which in turn blocks image removal due to active reference conflicts.

To recover and cleanly clear the stuck container:

1. Identify the stuck container ID:
```bash
docker ps -a | grep openbmc-numaker
```

2. Stop the Docker daemon:
```bash
sudo systemctl stop docker
```

3. Remove the stuck container metadata directory (replace `<CONTAINER_ID>` with the ID from step 1):
```bash
sudo rm -rf /var/lib/docker/containers/<CONTAINER_ID>*
```

4. Restart the Docker daemon:
```bash
sudo systemctl start docker
```

5. Force-remove the associated Docker image:
```bash
docker rmi -f openbmc-numaker-$(id -nu):v1
```

6. Clean up orphaned layers and build caches:
```bash
docker system prune -f
```

---

## 6. Important Notes & Gotchas

1. **Host-Container Shared Storage**:
   - The shared directory is located on the host at `~/shared` (`$HOME/shared`) and mounted inside the container at `/home/<username>/shared` (accessible as `~/shared`).
   - Always keep your repository, bitbake caches, and image outputs inside `~/shared`. Anything written outside `~/shared` (e.g. directly in `/tmp` or root) will be lost if the container is recreated.
2. **Permission Integrity**:
   - Because `build.sh` automatically configures the container user to match your host UID (`$(id -u)`), all files created by Bitbake will be owned by your host user without requiring `sudo` on the host.
3. **Build Duration & Network Fetching**:
   - Initial compilation takes between **1 to 3 hours** depending on CPU core count and network speed. Subsequent builds benefit from `sstate-cache` and complete in minutes.
   - If an upstream network timeout occurs during downloading, simply re-run `bitbake nuwriter-pack` to continue.
